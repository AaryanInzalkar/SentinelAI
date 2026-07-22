import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app import auth, models

# Setup in-memory test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sentinel.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in test DB
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_database():
    # Clean up databases before each test
    db = TestingSessionLocal()
    db.query(models.Incident).delete()
    db.query(models.Alert).delete()
    db.query(models.Zone).delete()
    db.query(models.Camera).delete()
    db.query(models.User).delete()
    db.commit()
    db.close()

def get_auth_headers(email="test@sentinel.ai", password="testpassword"):
    # Register user
    client.post("/api/auth/register", json={"email": email, "password": password})
    # Login
    response = client.post("/api/auth/login", data={"username": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_user_registration_and_login():
    response = client.post(
        "/api/auth/register",
        json={"email": "register@test.com", "password": "securepassword"}
    )
    assert response.status_code == 201
    assert response.json()["email"] == "register@test.com"

    # Try login
    login_response = client.post(
        "/api/auth/login",
        data={"username": "register@test.com", "password": "securepassword"}
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

def test_camera_crud():
    headers = get_auth_headers()
    
    # Create Camera
    camera_data = {
        "name": "Front Yard Cam",
        "connection_type": "webcam",
        "source_path": "0"
    }
    response = client.post("/api/cameras/", json=camera_data, headers=headers)
    assert response.status_code == 201
    camera_id = response.json()["id"]
    assert response.json()["name"] == "Front Yard Cam"
    
    # Get Cameras
    get_response = client.get("/api/cameras/", headers=headers)
    assert get_response.status_code == 200
    assert len(get_response.json()) >= 1
    
    # Update Camera
    update_data = {"name": "Front Yard Camera Updated"}
    put_response = client.put(f"/api/cameras/{camera_id}", json=update_data, headers=headers)
    assert put_response.status_code == 200
    assert put_response.json()["name"] == "Front Yard Camera Updated"
    
    # Delete Camera
    del_response = client.delete(f"/api/cameras/{camera_id}", headers=headers)
    assert del_response.status_code == 204

def test_zone_creation_and_deletion():
    headers = get_auth_headers()
    
    # Create a camera first
    camera_data = {"name": "Backdoor", "connection_type": "file", "source_path": "path.mp4"}
    cam_resp = client.post("/api/cameras/", json=camera_data, headers=headers)
    camera_id = cam_resp.json()["id"]
    
    # Create Zone
    zone_data = {
        "name": "Prohibited Area 1",
        "polygon_coordinates": "[[10, 10], [100, 10], [100, 100], [10, 100]]",
        "is_restricted": True
    }
    response = client.post(f"/api/zones/camera/{camera_id}", json=zone_data, headers=headers)
    assert response.status_code == 201
    zone_id = response.json()["id"]
    assert response.json()["name"] == "Prohibited Area 1"
    
    # Get Zones for Camera
    zones_resp = client.get(f"/api/zones/camera/{camera_id}", headers=headers)
    assert zones_resp.status_code == 200
    assert len(zones_resp.json()) == 1
    
    # Delete Zone
    del_resp = client.delete(f"/api/zones/{zone_id}", headers=headers)
    assert del_resp.status_code == 204

def test_dashboard_stats():
    headers = get_auth_headers()
    
    # Mock some data
    cam_resp = client.post("/api/cameras/", json={"name": "Cam 1", "connection_type": "webcam", "source_path": "0", "is_active": True}, headers=headers)
    camera_id = cam_resp.json()["id"]
    
    # Create alert and incident
    alert_resp = client.post("/api/alerts/", json={
        "camera_id": camera_id,
        "risk_score": 75,
        "description": "Intrusion",
        "explanation": "Object breached restricted boundary",
        "is_dismissed": False
    }, headers=headers)
    
    stats_resp = client.get("/api/dashboard/stats", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["active_cameras"] == 1
    assert stats["total_alerts_today"] == 1
    assert stats["unresolved_incidents"] == 1
