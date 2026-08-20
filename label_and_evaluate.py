"""
SentinelAI — Test Data Labeling + Accuracy Benchmark
======================================================
Wired to your actual pipeline: Detector -> Tracker -> FeatureExtractor -> RiskEngine
(matching backend/app/api/cameras.py's generate_frames() call order)

USAGE
-----
Step 1 — Record test footage:
  2-3 min of webcam footage: normal movement, plus loitering/fast-movement
  inside the zone you configure below.

Step 2 — Label it:
  python label_and_evaluate.py label --video test_footage.mp4 --every 1.0
  Press: n = normal, s = suspicious, q = quit and save

Step 3 — !! EDIT THE CONFIG BELOW !! — set ZONE_POLYGON to match the actual
  restricted zone location in your test footage (in pixel coordinates,
  matching your camera resolution). If you don't care about zone-based
  logic for this test, leave it as a small placeholder box — dwell/zone
  triggers just won't fire, and the eval will mostly reflect speed-only
  detection.

Step 4 — Evaluate:
  python label_and_evaluate.py evaluate --video test_footage.mp4 --labels labels.csv
"""

import argparse
import csv
import json
import sys
import time

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# CONFIG — edit these three things before running `evaluate`
# ---------------------------------------------------------------------------
MODEL_PATH = "yolov8n.pt"          # must match what detector.py actually loads
DETECTION_THRESHOLD = 0.25          # match camera.detection_threshold if you know it
LOITERING_THRESHOLD_SECONDS = 15    # match camera.loitering_threshold if you know it

# Restricted zone polygon, in pixel coords matching your test video's resolution.
# Draw/estimate this over where your "suspicious" behavior actually happens on screen.
ZONE_POLYGON = [[180, 180], [380, 180], [380, 320], [180, 320]]

DEBUG = False  # set True (or use --debug flag) to print per-frame speed/dwell/risk values
# ---------------------------------------------------------------------------


class MockZone:
    """Stand-in for models.Zone (DB row) — FeatureExtractor only needs these 4 attrs."""
    def __init__(self, zone_id, name, polygon_coords, is_restricted=True):
        self.id = zone_id
        self.name = name
        self.polygon_coordinates = json.dumps(polygon_coords)
        self.is_restricted = is_restricted


def label_mode(video_path, every_seconds, out_csv):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Could not open {video_path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_interval = max(1, int(fps * every_seconds))

    rows = []
    frame_idx = 0
    print("Labeling: press 'n' = normal, 's' = suspicious, 'q' = quit & save")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx % frame_interval == 0:
            display = frame.copy()
            cv2.putText(display, f"Frame {frame_idx} | n=normal s=suspicious q=quit",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Label frame", display)
            key = cv2.waitKey(0) & 0xFF

            if key == ord("q"):
                break
            elif key == ord("n"):
                rows.append({"frame_idx": frame_idx, "label": "normal"})
            elif key == ord("s"):
                rows.append({"frame_idx": frame_idx, "label": "suspicious"})

        frame_idx += 1

    cap.release()
    cv2.destroyAllWindows()

    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["frame_idx", "label"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} labels to {out_csv}")
    print(f"  normal: {sum(1 for r in rows if r['label'] == 'normal')}")
    print(f"  suspicious: {sum(1 for r in rows if r['label'] == 'suspicious')}")


def evaluate_mode(video_path, labels_csv):
    try:
        from sklearn.metrics import classification_report, accuracy_score
    except ImportError:
        print("scikit-learn required: pip install scikit-learn")
        sys.exit(1)

    # Import your actual pipeline components
    try:
        from backend.app.services.detector import Detector
        from backend.app.services.tracker import Tracker
        from backend.app.services.features import FeatureExtractor
        from backend.app.services.risk_engine import RiskEngine
    except ImportError as e:
        print(f"Could not import backend services: {e}")
        print("Run this script from the repo root, or adjust sys.path.")
        sys.exit(1)

    with open(labels_csv) as f:
        reader = csv.DictReader(f)
        labels = {int(row["frame_idx"]): row["label"] for row in reader}

    if not labels:
        print("No labels found — run 'label' mode first.")
        sys.exit(1)

    print(f"Loaded {len(labels)} labeled frames.")

    detector = Detector(model_name=MODEL_PATH)
    if not detector.load_model():
        print("WARNING: model failed to load — tracker will return no detections. "
              "Check MODEL_PATH.")

    tracker = Tracker()
    extractor = FeatureExtractor()
    risk_engine = RiskEngine()
    zones = [MockZone(1, "Test Restricted Zone", ZONE_POLYGON, is_restricted=True)]

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Could not open {video_path}")
        sys.exit(1)

    y_true, y_pred = [], []
    frame_idx = 0
    max_labeled_frame = max(labels.keys())

    print("Running pipeline frame-by-frame (this walks the whole video in order "
          "so tracking IDs / dwell time stay consistent — may take a bit)...")

    while frame_idx <= max_labeled_frame:
        ok, frame = cap.read()
        if not ok:
            break

        tracked = tracker.track(detector.model, frame, DETECTION_THRESHOLD)
        tracked = extractor.update(tracked, zones)
        tracked = risk_engine.evaluate_threats(tracked, LOITERING_THRESHOLD_SECONDS)

        if frame_idx in labels:
            # A frame is "predicted suspicious" if ANY tracked object is Warning/Critical.
            # (Matches how cameras.py triggers alerts — threat_level in Warning/Critical.)
            frame_threat_levels = [obj["threat_level"] for obj in tracked]
            predicted = "suspicious" if any(
                t in ("Warning", "Critical") for t in frame_threat_levels
            ) else "normal"

            y_true.append(labels[frame_idx])
            y_pred.append(predicted)

            if DEBUG:
                true_label = labels[frame_idx]
                mismatch = " <-- WRONG" if predicted != true_label else ""
                for obj in tracked:
                    zones_str = ", ".join(
                        f"{z['zone_name']}(dwell={z['dwell_time']:.1f}s)"
                        for z in obj.get("active_zones", {}).values()
                    ) or "none"
                    print(f"  frame={frame_idx:4d} true={true_label:10s} pred={predicted:10s}"
                          f" track_id={obj['track_id']:3d} speed={obj['speed']:6.1f}px/s"
                          f" zones=[{zones_str}] risk={obj['risk_score']:3d}"
                          f" level={obj['threat_level']:8s}{mismatch}")
                if not tracked:
                    print(f"  frame={frame_idx:4d} true={true_label:10s} pred={predicted:10s}"
                          f" (no tracked objects){mismatch}")

        frame_idx += 1

    cap.release()

    if not y_true:
        print("No labeled frames were reached during playback — check that "
              "labels.csv frame indices match this video.")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("ACCURACY EVALUATION")
    print("=" * 50)
    print(f"Frames evaluated: {len(y_true)}")
    print(f"Accuracy: {accuracy_score(y_true, y_pred):.1%}")
    print()
    print(classification_report(y_true, y_pred, zero_division=0))
    print("=" * 50)
    print(f'\nSuggested README/CV line:\n"Validated end-to-end risk classification at '
          f'{accuracy_score(y_true, y_pred):.0%} accuracy on a {len(y_true)}-frame '
          f'hand-labeled test set"')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Label test data and evaluate SentinelAI's risk engine")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    label_parser = subparsers.add_parser("label")
    label_parser.add_argument("--video", required=True)
    label_parser.add_argument("--every", type=float, default=1.0, help="Seconds between sampled frames")
    label_parser.add_argument("--out", default="labels.csv")

    eval_parser = subparsers.add_parser("evaluate")
    eval_parser.add_argument("--video", required=True)
    eval_parser.add_argument("--labels", default="labels.csv")
    eval_parser.add_argument("--debug", action="store_true",
                              help="Print per-frame speed/dwell/risk values to help tune thresholds")

    args = parser.parse_args()

    if args.mode == "label":
        label_mode(args.video, args.every, args.out)
    elif args.mode == "evaluate":
        if args.debug:
            DEBUG = True
        evaluate_mode(args.video, args.labels)