"""
LifeMetrics FastAPI Application.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis import redis_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting LifeMetrics application...")

    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_db()

        # Connect to Redis
        logger.info("Connecting to Redis...")
        await redis_client.connect()

        logger.info("Application started successfully!")
        yield

    finally:
        # Shutdown
        logger.info("Shutting down application...")

        # Disconnect from Redis
        await redis_client.disconnect()

        # Close database connections
        await close_db()

        logger.info("Application shutdown complete.")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Privacy-first AI-powered life analytics dashboard",
    version="0.1.0",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Gzip middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_healthy = True  # TODO: Add actual database health check
    redis_healthy = await redis_client.ping()

    return JSONResponse(
        status_code=200 if (db_healthy and redis_healthy) else 503,
        content={
            "status": "healthy" if (db_healthy and redis_healthy) else "unhealthy",
            "database": "ok" if db_healthy else "error",
            "redis": "ok" if redis_healthy else "error",
            "version": "0.1.0",
        },
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to LifeMetrics API",
        "version": "0.1.0",
        "docs": "/api/docs" if settings.debug else None,
    }


# API Router (to be implemented)
# from app.api import router as api_router
# app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug,
    )
