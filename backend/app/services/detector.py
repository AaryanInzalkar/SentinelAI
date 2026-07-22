import numpy as np
from typing import List, Dict, Any

class Detector:
    def __init__(self, model_name: str = "yolov8n.pt"):
        self.model_name = model_name
        self.model = None
        self.is_loaded = False
        
    def load_model(self) -> bool:
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_name)
            self.is_loaded = True
            print(f"YOLO model '{self.model_name}' loaded successfully.")
            return True
        except Exception as e:
            print(f"Failed to load YOLO model: {e}. Detector will operate in mock/pass-through mode.")
            self.model = None
            self.is_loaded = False
            return False
            
    def detect(self, frame: np.ndarray, conf_threshold: float = 0.25) -> List[Dict[str, Any]]:
        if not self.is_loaded or self.model is None:
            # Return empty list; if using synthetic video, we will extract simulated boxes directly
            return []
            
        try:
            results = self.model(frame, conf=conf_threshold, verbose=False)
            detections = []
            if results and len(results) > 0:
                result = results[0]
                boxes = result.boxes
                for box in boxes:
                    xyxy = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = result.names[cls]
                    
                    detections.append({
                        "box": [int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])],
                        "confidence": conf,
                        "class_id": cls,
                        "label": label
                    })
            return detections
        except Exception as e:
            print(f"Error during YOLO detection: {e}")
            return []
