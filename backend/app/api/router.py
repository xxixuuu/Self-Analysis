"""
Main API router combining all sub-routers.
"""
from fastapi import APIRouter

from app.api.routes import auth, dashboard, insights, oauth, sources

# Create main API router
api_router = APIRouter(prefix="/api")

# Include sub-routers
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(insights.router)
api_router.include_router(oauth.router)
api_router.include_router(sources.router)
