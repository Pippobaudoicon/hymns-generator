"""API routes package."""

from fastapi import APIRouter
from .hymns import router as hymns_router
from .wards import router as wards_router
from .health import router as health_router

# Main router that combines all sub-routers
router = APIRouter()

# Include all route modules
router.include_router(health_router, tags=["Health & Info"])
router.include_router(hymns_router, tags=["Hymns"])
router.include_router(wards_router, tags=["Wards"])
