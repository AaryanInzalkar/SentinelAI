import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./sentinel.db"
    SECRET_KEY: str = "supersecretkey_sentinelai_2026_dev_mode"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day for local MVP dev ease
    
    # AI Pipeline default parameters
    DEFAULT_LOITERING_THRESHOLD_SECONDS: int = 10
    DEFAULT_DETECTION_THRESHOLD: float = 0.25
    
    # Directory paths
    SNAPSHOT_DIR: str = os.path.join("backend", "data", "snapshots")
    VIDEO_DIR: str = os.path.join("backend", "data", "videos")
    
    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.SNAPSHOT_DIR, exist_ok=True)
os.makedirs(settings.VIDEO_DIR, exist_ok=True)
