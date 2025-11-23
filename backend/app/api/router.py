"""
Main API router combining all sub-routers.
"""
from fastapi import APIRouter

from app.api.routes import auth, dashboard, insights

# Create main API router
api_router = APIRouter(prefix="/api")

# Include sub-routers
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(insights.router)
