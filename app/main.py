from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.routes import search
from app.routes import upload
from app.routes import files 
from app.routes import watch
from app.processing.cache import ModelCache
from app.utils.watchdog_manager import watchdog_manager

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Pre-load AI models
    logger.info("Server booting up. Pre-loading AI models into RAM...")
    ModelCache.get_encoder()
    ModelCache.get_ocr_reader()
    logger.info("Models loaded successfully.")

    # 2. Start watchdog
    logger.info("Starting watchdog...")
    try:
        watchdog_manager.start()
    except Exception as e:
        logger.error(f"Watchdog failed to start: {e}")
        # Non-fatal — server continues without watchdog

    yield

    # 3. Stop watchdog
    logger.info("Shutting down...")
    try:
        watchdog_manager.stop()
    except Exception as e:
        logger.error(f"Watchdog failed to stop cleanly: {e}")

    logger.info("Shutdown complete.")

app = FastAPI(
    title="WhereTF Backend",
    lifespan=lifespan  # <-- Attach the hook here
)

app.include_router(search.router)
app.include_router(upload.router)
app.include_router(files.router)
app.include_router(watch.router)

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "WhereTF Backend",
        "database_connected": True 
    }