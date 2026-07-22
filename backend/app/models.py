import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    connection_type = Column(String, nullable=False)  # "webcam", "file", "ip_camera"
    source_path = Column(String, nullable=False)      # e.g., "0" or "video.mp4" or RTSP url
    is_active = Column(Boolean, default=True)
    detection_threshold = Column(Float, default=0.25)
    loitering_threshold = Column(Integer, default=10) # in seconds

    # Relationships
    zones = relationship("Zone", back_populates="camera", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="camera", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="camera", cascade="all, delete-orphan")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    polygon_coordinates = Column(Text, nullable=False)  # JSON string representation: "[[x1, y1], [x2, y2], ...]"
    is_restricted = Column(Boolean, default=True)

    # Relationships
    camera = relationship("Camera", back_populates="zones")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    risk_score = Column(Integer, default=0)              # 0 to 100
    description = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)            # Explainable AI summary text
    image_snapshot_path = Column(Text, nullable=True)     # Path to stored JPEG frame
    is_dismissed = Column(Boolean, default=False)

    # Relationships
    camera = relationship("Camera", back_populates="alerts")
    incidents = relationship("Incident", back_populates="alert", cascade="all, delete-orphan")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="Open")               # "Open", "Closed", "False Alarm"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    camera = relationship("Camera", back_populates="incidents")
    alert = relationship("Alert", back_populates="incidents")
