import numpy as np
from typing import List, Dict, Any

class Tracker:
    def __init__(self):
        # We can store track histories locally if needed for manual tracking fallback
        self.tracks = {}

    def track(self, model: Any, frame: np.ndarray, conf_threshold: float = 0.25) -> List[Dict[str, Any]]:
        """
        Runs tracking using Ultralytics YOLOv8 built-in tracker (ByteTrack/BoT-SORT).
        """
        if model is None:
            return []

        try:
            # Run YOLO track
            results = model.track(frame, persist=True, conf=conf_threshold, tracker="bytetrack.yaml", verbose=False)
            tracked_objects = []
            
            if results and len(results) > 0:
                result = results[0]
                boxes = result.boxes
                
                # Check if tracking IDs are present in the boxes
                if boxes is not None and hasattr(boxes, 'id') and boxes.id is not None:
                    ids = boxes.id.cpu().numpy().astype(int).tolist()
                    xyxy = boxes.xyxy.cpu().numpy().astype(int).tolist()
                    confs = boxes.conf.cpu().numpy().tolist()
                    clss = boxes.cls.cpu().numpy().astype(int).tolist()
                    
                    for i in range(len(ids)):
                        cls_id = clss[i]
                        label = result.names[cls_id]
                        tracked_objects.append({
                            "track_id": ids[i],
                            "box": xyxy[i],  # [x1, y1, x2, y2]
                            "confidence": confs[i],
                            "class_id": cls_id,
                            "label": label
                        })
                else:
                    # Fallback to standard detections if tracker IDs are not generated
                    # (e.g. first frame or tracking initialization)
                    for box in boxes:
                        xyxy = box.xyxy[0].cpu().numpy().astype(int).tolist()
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        label = result.names[cls]
                        tracked_objects.append({
                            "track_id": -1,  # Not tracked yet
                            "box": xyxy,
                            "confidence": conf,
                            "class_id": cls,
                            "label": label
                        })
            return tracked_objects
        except Exception as e:
            print(f"Error during tracking execution: {e}")
            return []
