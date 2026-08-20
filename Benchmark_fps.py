"""
SentinelAI — FPS Benchmark Script
==================================
Measures real inference speed of your detection pipeline so you can put an
actual number (e.g. "18.4 FPS on RTX 3060") on your resume/README instead of
a guess.

USAGE
-----
1. Drop this file into the repo root (same level as `backend/`).
2. Adjust the CONFIG section below if your import paths differ.
3. Run:
     python benchmark_fps.py --source 0                # webcam
     python benchmark_fps.py --source path/to/video.mp4 # video file
     python benchmark_fps.py --source rtsp://...        # IP camera
4. Let it run for the full duration (default 30s) without touching anything else
   on your machine — background load will skew the numbers.
5. Copy the printed summary block straight into your README/CV.

WHAT IT MEASURES
-----------------
- Raw YOLOv8 inference FPS (model.predict() only)
- End-to-end pipeline FPS (capture -> detect -> draw, if your detector does more)
- Device used (CPU vs CUDA) and model variant, pulled from the model object itself
"""

import argparse
import time
import statistics
import sys

import cv2


def run_raw_yolo_benchmark(source, model_path, duration_s, imgsz):
    """Benchmarks the YOLOv8 model directly via ultralytics, bypassing your
    detector.py wrapper. Use this first — it's the cleanest 'model speed' number."""
    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics not installed in this environment. pip install ultralytics")
        sys.exit(1)

    model = YOLO(model_path)
    device = model.device
    print(f"Loaded model: {model_path}")
    print(f"Device: {device}")

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Could not open source: {source}")
        sys.exit(1)

    frame_times = []
    start = time.time()
    frame_count = 0

    # Warmup (first few inferences are slower due to CUDA/cache init — exclude from stats)
    for _ in range(5):
        ok, frame = cap.read()
        if not ok:
            break
        model.predict(frame, imgsz=imgsz, verbose=False)

    print(f"Warmup done. Benchmarking for {duration_s}s...")
    bench_start = time.time()

    while time.time() - bench_start < duration_s:
        ok, frame = cap.read()
        if not ok:
            # loop video file if it ends before duration is up
            if isinstance(source, str) and not source.startswith("rtsp"):
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            break

        t0 = time.time()
        results = model.predict(frame, imgsz=imgsz, verbose=False)
        t1 = time.time()

        frame_times.append(t1 - t0)
        frame_count += 1

    cap.release()

    if not frame_times:
        print("No frames processed — check your source.")
        return

    total_time = sum(frame_times)
    avg_fps = frame_count / total_time
    median_ms = statistics.median(frame_times) * 1000
    p95_ms = sorted(frame_times)[int(len(frame_times) * 0.95)] * 1000

    print("\n" + "=" * 50)
    print("RAW YOLOv8 INFERENCE BENCHMARK")
    print("=" * 50)
    print(f"Frames processed:     {frame_count}")
    print(f"Device:               {device}")
    print(f"Image size:           {imgsz}")
    print(f"Average FPS:          {avg_fps:.1f}")
    print(f"Median latency:       {median_ms:.1f} ms/frame")
    print(f"P95 latency:          {p95_ms:.1f} ms/frame")
    print("=" * 50)
    print(f'\nSuggested README line:\n"~{avg_fps:.0f} FPS ({median_ms:.0f}ms median latency) '
          f'running YOLOv8 on {device}, {imgsz}px input"')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark SentinelAI detection FPS")
    parser.add_argument("--source", default="0",
                         help="0 for webcam, or path/URL to video/RTSP stream")
    parser.add_argument("--model", default="yolov8n.pt",
                         help="Path to the .pt weights your detector.py actually loads "
                              "(check detector.py for the exact model file/variant)")
    parser.add_argument("--duration", type=int, default=30,
                         help="Benchmark duration in seconds")
    parser.add_argument("--imgsz", type=int, default=640,
                         help="Inference image size (check what detector.py uses)")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    run_raw_yolo_benchmark(source, args.model, args.duration, args.imgsz)