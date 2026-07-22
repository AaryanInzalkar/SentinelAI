import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app import models, schemas, auth

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Active Cameras
    active_cameras_count = db.query(models.Camera).filter(models.Camera.is_active == True).count()
    
    # Total Alerts Today
    today_start = datetime.datetime.combine(datetime.datetime.now(datetime.timezone.utc).date(), datetime.time.min)
    alerts_today_count = db.query(models.Alert).filter(models.Alert.timestamp >= today_start).count()

    
    # Unresolved Incidents (status != "Closed")
    unresolved_incidents_count = db.query(models.Incident).filter(models.Incident.status != "Closed").count()
    
    # Simple overall health logic
    system_status = "Healthy"
    if active_cameras_count == 0:
        system_status = "Degraded (No Active Cameras)"
    elif unresolved_incidents_count > 5:
        system_status = "Warning (High Incident Volume)"
        
    return {
        "active_cameras": active_cameras_count,
        "total_alerts_today": alerts_today_count,
        "unresolved_incidents": unresolved_incidents_count,
        "system_status": system_status
    }
