"""Main FastAPI application for Italian Hymns API."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from hymns.exceptions import HymnAPIException
from config.settings import settings
from database.database import init_database

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
app.include_router(router, prefix=settings.API_PREFIX if hasattr(settings, 'API_PREFIX') else "")

# Root endpoint
@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "RESTful API for Italian hymns with smart selection",
        "docs_url": "/docs",
        "health_url": f"{getattr(settings, 'API_PREFIX', '')}/health",
        "features": [
            "Smart hymn selection avoiding 5-week repetition",
            "Ward-based hymn tracking",
            "Traditional hymn selection",
            "Historical hymn tracking"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "lds_tools:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_debug()
    )
