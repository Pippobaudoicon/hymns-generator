"""API routes for the Italian Hymns API."""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from datetime import datetime
import logging

from hymns.service import HymnService
from hymns.models import (
    Hymn, HymnList, HymnFilter, HymnSelectionRequest, 
    FestivityType
)
from hymns.exceptions import HymnAPIException
from config.settings import settings
from database.history_service import HymnHistoryService
from database.database import get_database_session
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter()

# Service dependency
def get_hymn_service() -> HymnService:
    """Dependency to get hymn service instance."""
    return HymnService(data_path=settings.get_data_path())

def get_history_service(hymn_service: HymnService = Depends(get_hymn_service)) -> HymnHistoryService:
    """Dependency to get hymn history service instance."""
    return HymnHistoryService(hymn_service)

@router.get("/get_hymns", response_model=HymnList, summary="Get hymns for service")
def get_hymns(
    prima_domenica: bool = Query(False, description="First Sunday of month (3 hymns instead of 4)"),
    domenica_festiva: bool = Query(False, description="Festive Sunday"),
    tipo_festivita: Optional[FestivityType] = Query(None, description="Type of festivity (required if domenica_festiva=true)"),
    service: HymnService = Depends(get_hymn_service)
) -> HymnList:
    """
    Generate a list of hymns for church service according to the rules:
    - 3 hymns for first Sunday (fast & testimony), 4 otherwise
    - Second hymn is always from Sacramento category
    - Special handling for festive Sundays
    
    Note: This endpoint does not use smart selection. Use /get_hymns_smart for ward-based selection.
    """
    try:
        hymns = service.get_hymns(prima_domenica, domenica_festiva, tipo_festivita)
        return HymnList(hymns=hymns)
    except HymnAPIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_hymns: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/get_hymns_smart", response_model=HymnList, summary="Get smart hymns for ward service")
def get_hymns_smart(
    ward_name: str = Query(..., description="Ward (congregation) name"),
    prima_domenica: bool = Query(False, description="First Sunday of month (3 hymns instead of 4)"),
    domenica_festiva: bool = Query(False, description="Festive Sunday"),
    tipo_festivita: Optional[FestivityType] = Query(None, description="Type of festivity (required if domenica_festiva=true)"),
    save_selection: bool = Query(True, description="Save this selection to database"),
    selection_date: Optional[str] = Query(None, description="Selection date (YYYY-MM-DD format, defaults to today)"),
    history_service: HymnHistoryService = Depends(get_history_service)
) -> HymnList:
    """
    Generate a smart list of hymns that avoids repetition within 5 weeks.
    
    This endpoint tracks hymn usage by ward and ensures the same hymns
    aren't repeated within a 5-Sunday window.
    """
    try:
        # Parse selection date if provided
        parsed_date = None
        if selection_date:
            try:
                parsed_date = datetime.strptime(selection_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Get smart hymn selection
        hymns = history_service.get_smart_hymns(
            ward_name=ward_name,
            prima_domenica=prima_domenica,
            domenica_festiva=domenica_festiva,
            tipo_festivita=tipo_festivita,
            selection_date=parsed_date
        )
        
        # Save selection if requested
        if save_selection:
            history_service.save_selection(
                ward_name=ward_name,
                hymns=hymns,
                prima_domenica=prima_domenica,
                domenica_festiva=domenica_festiva,
                tipo_festivita=tipo_festivita,
                selection_date=parsed_date
            )
        
        return HymnList(hymns=hymns)
        
    except HymnAPIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_hymns_smart: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/ward_history/{ward_name}", summary="Get hymn selection history for a ward")
def get_ward_history(
    ward_name: str,
    limit: int = Query(10, ge=1, le=50, description="Number of recent selections to return"),
    history_service: HymnHistoryService = Depends(get_history_service)
) -> dict:
    """Get recent hymn selection history for a specific ward."""
    try:
        selections = history_service.get_ward_history(ward_name, limit)
        # Convert to response format
        history = []
        for selection in selections:
            history.append({
                "date": selection['selection_date'].strftime("%Y-%m-%d"),
                "prima_domenica": selection['prima_domenica'],
                "domenica_festiva": selection['domenica_festiva'],
                "tipo_festivita": selection['tipo_festivita'],
                "hymns": selection['hymns']
            })
        
        return {
            "ward_name": ward_name,
            "history": history,
            "total_selections": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting ward history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ward history")

@router.get("/wards", response_model=List[str], summary="Get all ward names")
def get_wards(
    history_service: HymnHistoryService = Depends(get_history_service)
) -> List[str]:
    """Get list of all ward names that have hymn selections."""
    try:
        return history_service.get_all_wards()
    except Exception as e:
        logger.error(f"Error getting wards: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve wards")

@router.get("/get_hymn", response_model=Optional[Hymn], summary="Get single hymn by criteria")
def get_hymn(
    number: Optional[int] = Query(None, description="Hymn number"),
    category: Optional[str] = Query(None, description="Hymn category"),
    tag: Optional[str] = Query(None, description="Hymn tag"),
    service: HymnService = Depends(get_hymn_service)
) -> Optional[Hymn]:
    """
    Get a single hymn filtered by number, category, or tag.
    All criteria are applied with AND logic.
    If multiple hymns match, one is returned at random.
    """
    try:
        hymn_filter = HymnFilter(number=number, category=category, tag=tag)
        hymn = service.get_hymn(hymn_filter)
        return hymn
    except HymnAPIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_hymn: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/categories", response_model=List[str], summary="Get all available categories")
def get_categories(
    service: HymnService = Depends(get_hymn_service)
) -> List[str]:
    """Get all available hymn categories."""
    try:
        return service.get_categories()
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")

@router.get("/tags", response_model=List[str], summary="Get all available tags")
def get_tags(
    service: HymnService = Depends(get_hymn_service)
) -> List[str]:
    """Get all available hymn tags."""
    try:
        return service.get_tags()
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tags")

@router.get("/stats", summary="Get hymn collection statistics")
def get_stats(
    service: HymnService = Depends(get_hymn_service)
) -> dict:
    """Get statistics about the hymn collection."""
    try:
        return service.get_stats()
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@router.get("/health", summary="Health check endpoint")
def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "Italian Hymns API"}
