"""API routes package."""

from fastapi import APIRouter

from auth.organization_routes import router as org_router
# Import auth routes
from auth.routes import router as auth_router

from .health import router as health_router
from .hymns import router as hymns_router
from .wards import router as wards_router

# Main router that combines all sub-routers
router = APIRouter()

# Include all route modules
router.include_router(health_router, tags=["Health & Info"])
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(org_router, tags=["Organization"])
router.include_router(hymns_router, tags=["Hymns"])
router.include_router(wards_router, tags=["Wards"])
