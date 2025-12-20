"""Health and info endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from config.settings import settings
from hymns.service import HymnService

logger = logging.getLogger(__name__)

router = APIRouter()


# Service dependency
def get_hymn_service() -> HymnService:
    """Dependency to get hymn service instance."""
    return HymnService(data_path=settings.get_data_path())


@router.get("/health", summary="Health check endpoint")
def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "Italian Hymns API"}


@router.get("/stats", summary="Get hymn collection statistics")
def get_stats(service: HymnService = Depends(get_hymn_service)) -> dict:
    """Get statistics about the hymn collection."""
    try:
        return service.get_stats()
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get(
    "/categories", response_model=List[str], summary="Get all available categories"
)
def get_categories(service: HymnService = Depends(get_hymn_service)) -> List[str]:
    """Get all available hymn categories."""
    try:
        return service.get_categories()
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")


@router.get("/tags", response_model=List[str], summary="Get all available tags")
def get_tags(service: HymnService = Depends(get_hymn_service)) -> List[str]:
    """Get all available hymn tags."""
    try:
        return service.get_tags()
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tags")
