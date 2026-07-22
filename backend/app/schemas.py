from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str

# Zone Schemas
class ZoneBase(BaseModel):
    name: str
    polygon_coordinates: str  # JSON String representing [[x1,y1], [x2,y2], ...]
    is_restricted: Optional[bool] = True

class ZoneCreate(ZoneBase):
    pass

class ZoneResponse(ZoneBase):
    id: int
    camera_id: int

    class Config:
        from_attributes = True

# Camera Schemas
class CameraBase(BaseModel):
    name: str
    connection_type: str  # "webcam", "file", "ip_camera"
    source_path: str
    is_active: Optional[bool] = True
    detection_threshold: Optional[float] = 0.25
    loitering_threshold: Optional[int] = 10

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    connection_type: Optional[str] = None
    source_path: Optional[str] = None
    is_active: Optional[bool] = None
    detection_threshold: Optional[float] = None
    loitering_threshold: Optional[int] = None

class CameraResponse(CameraBase):
    id: int
    zones: List[ZoneResponse] = []

    class Config:
        from_attributes = True

# Alert Schemas
class AlertBase(BaseModel):
    camera_id: int
    risk_score: int
    description: Optional[str] = None
    explanation: Optional[str] = None
    image_snapshot_path: Optional[str] = None
    is_dismissed: Optional[bool] = False

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Incident Schemas
class IncidentBase(BaseModel):
    camera_id: int
    alert_id: int
    status: Optional[str] = "Open"
    notes: Optional[str] = None

class IncidentCreate(IncidentBase):
    pass

class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class IncidentResponse(IncidentBase):
    id: int
    created_at: datetime
    alert: Optional[AlertResponse] = None

    class Config:
        from_attributes = True

# Dashboard Stats Schemas
class DashboardStats(BaseModel):
    active_cameras: int
    total_alerts_today: int
    unresolved_incidents: int
    system_status: str
