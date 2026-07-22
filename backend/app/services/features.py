import cv2
import time
import json
import numpy as np
from typing import List, Dict, Any, Tuple

class FeatureExtractor:
    def __init__(self):
        # track_id -> dict containing centroids, timestamps, zone_entries
        self.track_history = {}
        self.max_history_age_seconds = 10.0  # clean up tracks not updated for 10s

    def update(self, tracked_objects: List[Dict[str, Any]], zones: List[Any]) -> List[Dict[str, Any]]:
        """
        Updates track histories and computes behavioral features (dwell time, speed, zone intersection).
        zones is a list of models.Zone objects.
        """
        current_time = time.time()
        self._cleanup_stale_tracks(current_time)
        
        updated_objects = []
        
        for obj in tracked_objects:
            track_id = obj["track_id"]
            box = obj["box"]  # [x1, y1, x2, y2]
            
            # 1. Compute bottom-center representing feet position
            x_center = (box[0] + box[2]) / 2.0
            y_feet = float(box[3])
            feet_position = (x_center, y_feet)
            
            # 2. Get or initialize history for this track
            if track_id not in self.track_history:
                self.track_history[track_id] = {
                    "centroids": [],
                    "timestamps": [],
                    "zone_entries": {}, # zone_id -> entry_timestamp
                    "last_seen": current_time
                }
                
            history = self.track_history[track_id]
            history["last_seen"] = current_time
            history["centroids"].append(feet_position)
            history["timestamps"].append(current_time)
            
            # Keep history within reasonable size (last 100 points)
            if len(history["centroids"]) > 100:
                history["centroids"].pop(0)
                history["timestamps"].pop(0)
                
            # 3. Calculate speed (pixels per second based on last 5 frames)
            speed = 0.0
            if len(history["centroids"]) >= 2:
                recent_pts = history["centroids"][-5:]
                recent_times = history["timestamps"][-5:]
                dist = 0.0
                for i in range(len(recent_pts) - 1):
                    p1 = np.array(recent_pts[i])
                    p2 = np.array(recent_pts[i+1])
                    dist += np.linalg.norm(p2 - p1)
                time_diff = recent_times[-1] - recent_times[0]
                if time_diff > 0.01:
                    speed = dist / time_diff
                    
            # 4. Check restricted zone containment and calculate dwell times
            active_zones = {}
            for zone in zones:
                try:
                    coords = json.loads(zone.polygon_coordinates)
                    if len(coords) < 3:
                        continue
                    
                    # Convert to cv2 format (numpy array of shape (N, 1, 2) and type int32)
                    pts = np.array(coords, dtype=np.int32).reshape((-1, 1, 2))
                    
                    # Run point polygon test (returns >= 0 if inside or on edge)
                    is_inside = cv2.pointPolygonTest(pts, feet_position, False) >= 0
                    
                    if is_inside:
                        if zone.id not in history["zone_entries"]:
                            # Just entered zone
                            history["zone_entries"][zone.id] = current_time
                        
                        # Calculate dwell time
                        dwell_time = current_time - history["zone_entries"][zone.id]
                        active_zones[zone.id] = {
                            "zone_name": zone.name,
                            "is_restricted": zone.is_restricted,
                            "dwell_time": dwell_time
                        }
                    else:
                        # Left zone (or not in it)
                        if zone.id in history["zone_entries"]:
                            history["zone_entries"].pop(zone.id)
                except Exception as e:
                    print(f"Error parsing polygon for zone {zone.id}: {e}")
                    
            # Append behavior features to object dict
            obj_features = obj.copy()
            obj_features["feet_position"] = feet_position
            obj_features["speed"] = speed
            obj_features["active_zones"] = active_zones
            updated_objects.append(obj_features)
            
        return updated_objects
        
    def _cleanup_stale_tracks(self, current_time: float):
        stale_ids = []
        for track_id, history in self.track_history.items():
            if current_time - history["last_seen"] > self.max_history_age_seconds:
                stale_ids.append(track_id)
        for track_id in stale_ids:
            self.track_history.pop(track_id)
            
    def get_track_history_path(self, track_id: int) -> List[Tuple[float, float]]:
        if track_id in self.track_history:
            return self.track_history[track_id]["centroids"]
        return []
