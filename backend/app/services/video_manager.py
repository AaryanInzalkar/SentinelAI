import cv2
import time
import os
import numpy as np
from typing import Generator, Tuple, Optional

class VideoManager:
    def __init__(self, source_path: str, connection_type: str):
        self.source_path = source_path
        self.connection_type = connection_type
        self.cap = None
        self.is_running = False
        
        # Simulated scenario variables (for synthetic fallback mode)
        self.sim_start_time = time.time()
        self.sim_objects = [
            # {"id": 1, "path": function of time -> (x, y), "class": "person"}
            {"id": 101, "start_delay": 0, "speed": 100, "y_pos": 250, "type": "passerby"},
            {"id": 102, "start_delay": 5, "speed": 50, "y_pos": 150, "type": "loiterer"}
        ]
        
    def open_source(self) -> bool:
        if self.connection_type == "webcam":
            try:
                # Typically webcam is index 0
                idx = int(self.source_path)
                self.cap = cv2.VideoCapture(idx)
            except ValueError:
                self.cap = cv2.VideoCapture(0)
        elif self.connection_type == "file":
            if os.path.exists(self.source_path):
                self.cap = cv2.VideoCapture(self.source_path)
            else:
                # File does not exist, use synthetic fallback
                self.cap = None
        elif self.connection_type == "ip_camera":
            self.cap = cv2.VideoCapture(self.source_path)
        else:
            self.cap = None
            
        if self.cap and self.cap.isOpened():
            self.is_running = True
            return True
        else:
            print(f"Video Source '{self.source_path}' could not be opened. Using high-tech synthetic simulation mode.")
            self.cap = None
            self.is_running = True
            return True # Allow running in simulation mode
            
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.is_running:
            return False, None
            
        if self.cap is not None:
            ret, frame = self.cap.read()
            if not ret:
                # Loop video files if they reach the end
                if self.connection_type == "file":
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                    return ret, frame
                return False, None
            return True, frame
        else:
            # Generate synthetic frame
            frame = self._generate_synthetic_frame()
            time.sleep(0.04) # Simulate ~25 FPS
            return True, frame
            
    def release(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
            
    def _generate_synthetic_frame(self) -> np.ndarray:
        # Create a sleek dark-navy background frame (640x480)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw background color (navy tint: RGB 10, 15, 30)
        frame[:] = [30, 15, 10]  # OpenCV uses BGR: Blue=30, Green=15, Red=10
        
        # Draw subtle grid lines to make it look technical/surveillance-like
        grid_color = (45, 25, 15)  # Subtle navy grid lines
        for x in range(0, 640, 40):
            cv2.line(frame, (x, 0), (x, 480), grid_color, 1)
        for y in range(0, 480, 40):
            cv2.line(frame, (0, y), (640, y), grid_color, 1)
            
        # Draw simulated restricted zone outline
        # Coordinates: [[50, 50], [300, 50], [300, 300], [50, 300]]
        poly_pts = np.array([[50, 50], [300, 50], [300, 300], [50, 300]], np.int32)
        poly_pts = poly_pts.reshape((-1, 1, 2))
        
        # Pulsing restricted zone outline
        pulse = int(127 + 127 * np.sin(time.time() * 3))
        zone_color = (0, pulse, 255) if pulse > 100 else (0, 0, 200) # Orange-Red pulse
        cv2.polylines(frame, [poly_pts], True, zone_color, 2)
        
        # Transparent fill for restricted zone
        overlay = frame.copy()
        cv2.fillPoly(overlay, [poly_pts], (0, 0, 80))  # Semi-transparent red overlay
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        
        # Text label for the zone
        cv2.putText(frame, "RESTRICTED ZONE A", (60, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 1, cv2.LINE_AA)
        
        # Simulate moving targets
        elapsed = time.time() - self.sim_start_time
        
        for obj in self.sim_objects:
            if elapsed < obj["start_delay"]:
                continue
                
            obj_elapsed = elapsed - obj["start_delay"]
            
            if obj["type"] == "passerby":
                # Linear path from left to right, never staying inside zone
                # x starts at -50, moves to 700, then repeats
                x = int(-50 + (obj_elapsed * obj["speed"])) % 800
                if x > 750:
                    continue # Off screen
                y = obj["y_pos"]
                
                # Draw person box (green)
                w, h = 60, 140
                self._draw_sim_box(frame, obj["id"], "person", x, y, w, h, (0, 255, 0))
                
            elif obj["type"] == "loiterer":
                # Moves in from right, goes into restricted zone, stops, then exits
                # Total loop duration: 40 seconds
                cycle_time = obj_elapsed % 40
                w, h = 70, 150
                
                if cycle_time < 5:
                    # Walking in: from x=550 to x=180
                    progress = cycle_time / 5.0
                    x = int(550 - progress * (550 - 180))
                    y = obj["y_pos"]
                    box_color = (0, 255, 0)
                elif cycle_time < 25:
                    # Standing in zone: x=180, y=150. Status is loitering!
                    x = 180
                    y = obj["y_pos"]
                    # Color changes to warning/danger (red) if loitering > 5s
                    loiter_duration = cycle_time - 5
                    if loiter_duration > 5:
                        box_color = (0, 0, 255) # Red box
                    else:
                        box_color = (0, 165, 255) # Orange box
                else:
                    # Walking away: from x=180 to x=-100
                    progress = (cycle_time - 25) / 15.0
                    x = int(180 - progress * (180 + 100))
                    y = obj["y_pos"]
                    box_color = (0, 255, 0)
                    
                if x > -100:
                    self._draw_sim_box(frame, obj["id"], "person", x, y, w, h, box_color)
                    
        # Add telemetry overlays
        cv2.rectangle(frame, (10, 10), (250, 45), (15, 10, 5), -1)
        cv2.putText(frame, "SENTINEL-AI FEED SIMULATOR", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, time.strftime("%Y-%m-%d %H:%M:%S"), (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)
        
        return frame
        
    def _draw_sim_box(self, frame: np.ndarray, obj_id: int, label: str, x: int, y: int, w: int, h: int, color: Tuple[int, int, int]):
        # Bounding box coordinates
        x1, y1 = x - w // 2, y - h // 2
        x2, y2 = x + w // 2, y + h // 2
        
        # Clip coordinates to frame boundaries
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(640, x2), min(480, y2)
        
        # Bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Tag header
        tag = f"{label} #{obj_id}"
        cv2.rectangle(frame, (x1, y1 - 20), (x1 + 100, y1), color, -1)
        cv2.putText(frame, tag, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

    def get_simulated_objects(self) -> List[Dict[str, Any]]:
        """
        Returns bounding boxes and tracker IDs for simulated targets at the current timestamp.
        """
        if self.cap is not None:
            return []
            
        elapsed = time.time() - self.sim_start_time
        tracked_objects = []
        
        for obj in self.sim_objects:
            if elapsed < obj["start_delay"]:
                continue
                
            obj_elapsed = elapsed - obj["start_delay"]
            
            if obj["type"] == "passerby":
                x = int(-50 + (obj_elapsed * obj["speed"])) % 800
                if x > 750:
                    continue
                y = obj["y_pos"]
                w, h = 60, 140
                
            elif obj["type"] == "loiterer":
                cycle_time = obj_elapsed % 40
                w, h = 70, 150
                if cycle_time < 5:
                    progress = cycle_time / 5.0
                    x = int(550 - progress * (550 - 180))
                    y = obj["y_pos"]
                elif cycle_time < 25:
                    x = 180
                    y = obj["y_pos"]
                else:
                    progress = (cycle_time - 25) / 15.0
                    x = int(180 - progress * (180 + 100))
                    y = obj["y_pos"]
                    
                if x <= -100:
                    continue
                    
            # Compute box xyxy
            x1, y1 = x - w // 2, y - h // 2
            x2, y2 = x + w // 2, y + h // 2
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(640, x2), min(480, y2)
            
            tracked_objects.append({
                "track_id": obj["id"],
                "box": [x1, y1, x2, y2],
                "confidence": 0.95,
                "class_id": 0,
                "label": "person"
            })
            
        return tracked_objects

