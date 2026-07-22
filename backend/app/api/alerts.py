from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app import models, schemas, auth

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

@router.get("/", response_model=List[schemas.AlertResponse])
def get_alerts(
    camera_id: Optional[int] = None,
    is_dismissed: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.Alert)
    if camera_id is not None:
        query = query.filter(models.Alert.camera_id == camera_id)
    if is_dismissed is not None:
        query = query.filter(models.Alert.is_dismissed == is_dismissed)
    return query.order_by(models.Alert.timestamp.desc()).all()

@router.get("/{alert_id}", response_model=schemas.AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.put("/{alert_id}/dismiss", response_model=schemas.AlertResponse)
def dismiss_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_dismissed = True
    db.commit()
    db.refresh(alert)
    return alert

@router.post("/", response_model=schemas.AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_in: schemas.AlertCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    camera = db.query(models.Camera).filter(models.Camera.id == alert_in.camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    alert = models.Alert(**alert_in.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    # Automatically create an incident for high-risk alerts (e.g. risk score > 50)
    if alert.risk_score >= 50:
        incident = models.Incident(
            camera_id=alert.camera_id,
            alert_id=alert.id,
            status="Open",
            notes=f"Auto-generated incident from high-risk alert (score: {alert.risk_score})"
        )
        db.add(incident)
        db.commit()

    return alert
