"""FastAPI application configuration"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from reversi_backend.config import settings
from reversi_backend.game_manager import game_manager
from reversi_backend.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def garbage_collection_task():
    """Background task to periodically clean up inactive games"""
    while True:
        try:
            await asyncio.sleep(settings.GC_INTERVAL_SECONDS)
            deleted_count = game_manager.collect_garbage(settings.GAME_TIMEOUT_SECONDS)
            if deleted_count > 0:
                logger.info(f"GC task: cleaned up {deleted_count} inactive games")
        except Exception as e:
            logger.error(f"Error in garbage collection task: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan and background tasks"""
    # Start background task
    gc_task = asyncio.create_task(garbage_collection_task())
    logger.info("Started garbage collection background task")

    yield

    # Cleanup on shutdown
    gc_task.cancel()
    try:
        await gc_task
    except asyncio.CancelledError:
        logger.info("Garbage collection task cancelled")


app: FastAPI = FastAPI(title="Reversi Backend API", version="1.0.0", lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,  # Load from settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Reversi Backend API", "version": "1.0.0"}
