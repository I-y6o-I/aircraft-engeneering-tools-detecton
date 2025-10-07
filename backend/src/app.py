from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.settings import settings
from .core.logging import setup_logging
from .api.routers import predict
from .api.routers import sessions
import logging
from contextlib import asynccontextmanager
from .api.routers import auth as auth_router
from .ml.yolo_service import initialize_yolo_service


# init logging early
setup_logging()
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.APP_NAME)
    
    # Initialize YOLO model at startup
    if settings.USE_YOLO:
        logger.info("Initializing YOLO model...")
        yolo_initialized = initialize_yolo_service()
        if yolo_initialized:
            logger.info("✅ YOLO model loaded and ready for inference!")
        else:
            logger.warning("⚠️ YOLO model failed to load, will fallback to stub")
    else:
        logger.info("YOLO disabled, using stub inference")
    
    yield
    logger.info("Shutting down %s", settings.APP_NAME)

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    # Увеличиваем максимальный размер запроса до 100MB
    max_request_size=52428800*2
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/healthz")
async def healthz():
    # DB не обязателен; если задан, можно добавить ping позже
    return {"status": "ok"}

@app.get("/version")
async def version():
    return {"name": settings.APP_NAME, "version": "0.0.1"}

@app.get("/ml/status")
async def ml_status():
    """Check ML model status."""
    try:
        from .ml.yolo_service import _yolo_service
        if _yolo_service is not None and _yolo_service.model is not None:
            return {
                "yolo_enabled": settings.USE_YOLO,
                "model_loaded": True,
                "model_path": _yolo_service.model_path,
                "model_classes": len(_yolo_service.model.names) if _yolo_service.model else 0,
                "status": "ready"
            }
        else:
            return {
                "yolo_enabled": settings.USE_YOLO,
                "model_loaded": False,
                "status": "using_stub"
            }
    except Exception as e:
        return {
            "yolo_enabled": settings.USE_YOLO,
            "model_loaded": False,
            "error": str(e),
            "status": "error"
        }

# Routers
app.include_router(predict.router, prefix="", tags=["predict"])
app.include_router(auth_router.router)
app.include_router(sessions.router)