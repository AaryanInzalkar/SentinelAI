import os
import json
import time
import numpy as np
import cv2
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from backend.app.database import get_db, SessionLocal
from backend.app import models, schemas, auth
from backend.app.config import settings

router = APIRouter(prefix="/api/cameras", tags=["cameras"])

@router.get("/", response_model=List[schemas.CameraResponse])
def get_cameras(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.Camera).all()

@router.get("/{camera_id}", response_model=schemas.CameraResponse)
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera

@router.post("/", response_model=schemas.CameraResponse, status_code=status.HTTP_201_CREATED)
def create_camera(
    camera_in: schemas.CameraCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    camera = models.Camera(**camera_in.model_dump())
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera

@router.put("/{camera_id}", response_model=schemas.CameraResponse)
def update_camera(
    camera_id: int,
    camera_in: schemas.CameraUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    update_data = camera_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(camera, key, value)
    
    db.commit()
    db.refresh(camera)
    return camera

@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    db.delete(camera)
    db.commit()
    return None

# Video Stream Generator Loop running the full ML pipeline per frame
def generate_frames(camera_id: int):
    # Open private database session for this stream generator
    db = SessionLocal()
    
    # Fetch camera details
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        db.close()
        return
        
    # Import components inside generator to prevent circular imports and keep dependencies modular
    from backend.app.services.video_manager import VideoManager
    from backend.app.services.detector import Detector
    from backend.app.services.tracker import Tracker
    from backend.app.services.features import FeatureExtractor
    from backend.app.services.risk_engine import RiskEngine
    from backend.app.services.explainer import Explainer
    
    video_manager = VideoManager(camera.source_path, camera.connection_type)
    if not video_manager.open_source():
        db.close()
        return
        
    detector = Detector()
    detector.load_model()  # Will log error and run fallback if ultralytics is not available
    tracker = Tracker()
    extractor = FeatureExtractor()
    risk_engine = RiskEngine()
    
    # Store logged alert timestamps per track_id to prevent duplicates (15-second cooldown)
    last_alerts_logged = {}
    
    try:
        while video_manager.is_running:
            ret, frame = video_manager.read_frame()
            if not ret:
                break
                
            # Periodically reload camera config/zones in case of settings changes
            camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
            if not camera or not camera.is_active:
                break
                
            zones = camera.zones
            
            # Capture tracking detections
            if video_manager.cap is not None:
                # Real camera feed
                tracked_objects = tracker.track(detector.model, frame, camera.detection_threshold)
            else:
                # Synthetic simulated feed
                tracked_objects = video_manager.get_simulated_objects()
                
            # Process behavior features (dwell time, speed, zone presence)
            tracked_objects = extractor.update(tracked_objects, zones)
            
            # Predict risk using ML model
            tracked_objects = risk_engine.evaluate_threats(tracked_objects, camera.loitering_threshold)
            
            current_time = time.time()
            
            # Draw object boxes & analyze threats
            for obj in tracked_objects:
                track_id = obj["track_id"]
                risk_score = obj["risk_score"]
                threat_level = obj["threat_level"]
                triggers = obj["triggers"]
                box = obj["box"]
                speed = obj["speed"]
                
                # Determine colors (BGR format for OpenCV)
                if threat_level == "Critical":
                    color = (0, 0, 255)       # Red
                elif threat_level == "Warning":
                    color = (0, 165, 255)     # Orange
                else:
                    color = (0, 255, 0)       # Green
                    
                x1, y1, x2, y2 = box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Draw tag header label
                tag_text = f"{obj['label']} #{track_id} | Risk: {risk_score}% | Speed: {speed:.1f}px/s"
                cv2.rectangle(frame, (x1, y1 - 22), (x1 + len(tag_text) * 8, y1), color, -1)
                cv2.putText(frame, tag_text, (x1 + 4, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
                
                # Threat escalation log
                if threat_level in ["Warning", "Critical"]:
                    last_alert_time = last_alerts_logged.get(track_id, 0.0)
                    if current_time - last_alert_time > 15.0:
                        # Extract zone details
                        zone_name = "Restricted Zone"
                        dwell_time = 0.0
                        if obj.get("active_zones"):
                            zone_id = list(obj["active_zones"].keys())[0]
                            zone_name = obj["active_zones"][zone_id]["zone_name"]
                            dwell_time = obj["active_zones"][zone_id]["dwell_time"]
                            
                        # Generate natural language AI explanation
                        explanation = Explainer.generate_explanation(
                            track_id=track_id,
                            label=obj["label"],
                            risk_score=risk_score,
                            threat_level=threat_level,
                            triggers=triggers,
                            speed=speed,
                            dwell_time=dwell_time,
                            zone_name=zone_name
                        )
                        
                        # Log alert in database
                        new_alert = models.Alert(
                            camera_id=camera_id,
                            risk_score=risk_score,
                            description=f"Threat detected: {obj['label']} #{track_id} ({', '.join(triggers)})",
                            explanation=explanation,
                            is_dismissed=False
                        )
                        db.add(new_alert)
                        db.commit()
                        db.refresh(new_alert)
                        
                        # Save JPEG snapshot frame to disk
                        snapshot_filename = f"alert_{new_alert.id}_{int(current_time)}.jpg"
                        snapshot_path = os.path.join(settings.SNAPSHOT_DIR, snapshot_filename)
                        cv2.imwrite(snapshot_path, frame)
                        
                        # Link snapshot path in db
                        new_alert.image_snapshot_path = snapshot_path
                        db.commit()
                        
                        # Generate an Incident for Critical threats (Score >= 70)
                        if risk_score >= 70:
                            new_incident = models.Incident(
                                camera_id=camera_id,
                                alert_id=new_alert.id,
                                status="Open",
                                notes=f"Automatic alert response escalates Threat #{track_id} to Active Incident status."
                            )
                            db.add(new_incident)
                            db.commit()
                            
                        last_alerts_logged[track_id] = current_time
            
            # Draw drawn zones
            for zone in zones:
                try:
                    coords = json.loads(zone.polygon_coordinates)
                    if len(coords) < 3:
                        continue
                    pts = np.array(coords, dtype=np.int32).reshape((-1, 1, 2))
                    # Draw polygon lines
                    cv2.polylines(frame, [pts], True, (0, pulse_color(current_time), 255) if zone.is_restricted else (0, 255, 0), 2)
                    label_pt = coords[0]
                    cv2.putText(frame, zone.name, (label_pt[0], label_pt[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1, cv2.LINE_AA)
                except Exception:
                    pass
            
            # Encode frame to JPEG
            ret_encode, jpeg_buffer = cv2.imencode('.jpg', frame)
            if not ret_encode:
                continue
                
            jpeg_bytes = jpeg_buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
                   
    finally:
        video_manager.release()
        db.close()

def pulse_color(t: float) -> int:
    return int(127 + 127 * np.sin(t * 3.0))

@router.get("/{camera_id}/stream")
def stream_camera(camera_id: int, db: Session = Depends(get_db)):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    return StreamingResponse(
        generate_frames(camera_id), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/{camera_id}/snapshot")
def get_camera_snapshot(camera_id: int):
    import io
    db = SessionLocal()
    try:
        camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
            
        from backend.app.services.video_manager import VideoManager
        video_manager = VideoManager(camera.source_path, camera.connection_type)
        if not video_manager.open_source():
            raise HTTPException(status_code=500, detail="Could not open camera source")
            
        ret, frame = video_manager.read_frame()
        video_manager.release()
        
        if not ret:
            raise HTTPException(status_code=500, detail="Could not capture frame from source")
            
        # Encode frame as JPEG
        ret_encode, jpeg_buffer = cv2.imencode('.jpg', frame)
        if not ret_encode:
            raise HTTPException(status_code=500, detail="Failed to encode frame")
            
        return StreamingResponse(io.BytesIO(jpeg_buffer.tobytes()), media_type="image/jpeg")
    finally:
        db.close()

