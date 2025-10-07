from typing import List, Optional, Union
from datetime import timedelta
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    # Display name (Swagger)
    APP_NAME: str = "Aero Kit Check Backend"

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:8080", "http://127.0.0.1:8080", "*"]

    # External services / security / DB
    DATABASE_URL: Optional[str] = None  # e.g. postgresql+asyncpg://user:pass@localhost:5432/akc
    ML_ENDPOINT: Optional[str] = None   # e.g. http://ml:9000/infer

    # JWT settings (used for /auth)
    JWT_SECRET: str = "change-me-in-prod"
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_SECONDS: int = 60 * 60 * 8  # 8h

    # Classes catalog (11)
    CLASSES: List[str] = [
        "screwdriver_plus","wrench_adjustable","offset_cross","ring_wrench_3_4",
        "nippers","brace","lock_pliers","pliers","shernitsa","screwdriver_minus","oil_can_opener"
    ]
    
    # ML Model settings
    MODEL_PATH: Optional[str] = None  # Path to YOLO .pt file (auto-detect if None)
    USE_YOLO: bool = True  # Enable/disable YOLO inference
    YOLO_CONFIDENCE_THRESHOLD: float = 0.25  # Base YOLO confidence threshold for all detections

    YOLO_CONFIDENCE_THRESHOLD = 0.25
    # pydantic v2 settings config
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Helpers to parse CSV/JSON from .env
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors(cls, v: Union[str, List[str]]):
        """Allow comma-separated or JSON array in .env."""
        if v is None:
            return ["*"]
        if isinstance(v, list):
            return v
        v = v.strip()
        if v == "*":
            return ["*"]
        if v.startswith("["):
            import json
            return json.loads(v)
        return [s.strip() for s in v.split(",") if s.strip()]

    @field_validator("CLASSES", mode="before")
    @classmethod
    def _parse_classes(cls, v: Union[str, List[str]]):
        """Allow comma-separated or JSON array in .env."""
        if v is None or isinstance(v, list):
            return v
        v = v.strip()
        if v.startswith("["):
            import json
            return json.loads(v)
        return [s.strip() for s in v.split(",") if s.strip()]

def jwt_exp_delta() -> timedelta:
    """Return timedelta for access token TTL."""
    return timedelta(seconds=Settings().JWT_EXPIRES_SECONDS)

settings = Settings()