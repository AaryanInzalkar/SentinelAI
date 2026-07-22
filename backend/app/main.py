from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database import engine, Base, SessionLocal
from backend.app.config import settings
from backend.app import models, auth

from backend.app.api import auth as api_auth, cameras, zones, alerts, incidents, dashboard

# Build all tables on startup (simple SQLite migrations for MVP)
Base.metadata.create_all(bind=engine)

# Seed default admin user and dummy camera if DB empty
def seed_database():
    db = SessionLocal()
    try:
        # Check if default user exists
        user = db.query(models.User).filter(models.User.email == "admin@sentinel.ai").first()
        if not user:
            admin_user = models.User(
                email="admin@sentinel.ai",
                hashed_password=auth.get_password_hash("admin123")
            )
            db.add(admin_user)
            db.commit()
            print("Seeded default user admin@sentinel.ai / admin123")
            
        # Check if default camera exists
        camera = db.query(models.Camera).filter(models.Camera.name == "Mock Video Feed").first()
        if not camera:
            mock_camera = models.Camera(
                name="Mock Video Feed",
                connection_type="file",
                source_path="mock_video.mp4",
                is_active=True,
                detection_threshold=0.25,
                loitering_threshold=10
            )
            db.add(mock_camera)
            db.commit()
            db.refresh(mock_camera)
            print(f"Seeded default camera: ID {mock_camera.id}")
            
            # Seed default zone for mock camera
            # A mock zone coordinates as a polygon
            polygon = "[[50, 50], [300, 50], [300, 300], [50, 300]]"
            zone = models.Zone(
                camera_id=mock_camera.id,
                name="Main Entrance Zone",
                polygon_coordinates=polygon,
                is_restricted=True
            )
            db.add(zone)
            db.commit()
            print("Seeded default zone coordinates")
    finally:
        db.close()

seed_database()

# Initialize FastAPI App
app = FastAPI(
    title="SentinelAI Backend API",
    description="AI-powered surveillance intelligence engine",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
from fastapi.staticfiles import StaticFiles
app.mount("/snapshots", StaticFiles(directory=settings.SNAPSHOT_DIR), name="snapshots")

app.include_router(api_auth.router)

app.include_router(cameras.router)
app.include_router(zones.router)
app.include_router(alerts.router)
app.include_router(incidents.router)
app.include_router(dashboard.router)

@app.get("/")
def root():
    return {"message": "SentinelAI API is active and healthy."}
