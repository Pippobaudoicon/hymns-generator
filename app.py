"""
Main FastAPI application for Italian Hymns API.

This module initializes and configures the FastAPI application,
including middleware, exception handlers, and route registration.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router
from auth.organization_routes import router as org_router
from auth.routes import router as auth_router
from config.settings import settings
from database.database import init_database
from hymns.exceptions import HymnAPIException

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.is_debug() else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting Italian Hymns API")
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    logger.info("Shutting down Italian Hymns API")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="RESTful API for generating and retrieving Italian hymns for the Church of Jesus Christ with smart selection to avoid repetition",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(HymnAPIException)
async def hymn_api_exception_handler(request: Request, exc: HymnAPIException):
    """Handle custom hymn API exceptions."""
    logger.warning(f"API Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# Include API router
app.include_router(router, prefix=settings.API_PREFIX)

# Include auth routes at root level (without /api/v1 prefix)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(org_router, tags=["Organization"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Service Worker endpoint (must be at root to control entire site)
@app.get("/sw.js", tags=["PWA"])
def service_worker():
    """Serve the service worker script from root."""
    return FileResponse("static/sw.js", media_type="application/javascript")

# Root endpoint - redirect to login (login page handles redirect to dashboard if authenticated)
@app.get("/", tags=["Root"])
def read_root():
    """Redirect to login page."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login")

# Dashboard page
@app.get("/dashboard", tags=["Root"])
def dashboard_page():
    """Serve the tools dashboard."""
    return FileResponse("static/dashboard.html")

# Hymns selector page (individual tool)
@app.get("/hymns", tags=["Root"])
def hymns_page():
    """Serve the hymn selector web interface."""
    return FileResponse("static/hymns.html")

# Hymn player page (individual tool)
@app.get("/hymn-player", tags=["Root"])
def hymn_player_page():
    """Serve the hymn player web interface."""
    return FileResponse("static/hymn-player.html")

# Login page
@app.get("/login", tags=["Root"])
def login_page():
    """Serve the login page."""
    return FileResponse("static/login.html")

# Admin page
@app.get("/admin", tags=["Root"])
def admin_page():
    """Serve the admin page."""
    return FileResponse("static/admin.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_debug()
    )
