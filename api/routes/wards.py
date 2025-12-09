"""Ward management and history endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from config.settings import settings
from database.database import get_database_session
from database.history_service import HymnHistoryService
from database.models import Ward
from hymns.service import HymnService

logger = logging.getLogger(__name__)

router = APIRouter()

# Service dependencies
def get_hymn_service() -> HymnService:
    """Dependency to get hymn service instance."""
    return HymnService(data_path=settings.get_data_path())

def get_history_service(hymn_service: HymnService = Depends(get_hymn_service)) -> HymnHistoryService:
    """Dependency to get hymn history service instance."""
    return HymnHistoryService(hymn_service)

# --- Ward CRUD Operations ---

@router.get("/wards", response_model=List[str], summary="Get all ward names")
def get_wards(db: Session = Depends(get_database_session)) -> List[str]:
    """Get list of all ward names from the database."""
    try:
        wards = db.query(Ward).order_by(Ward.name).all()
        return [str(w.name) for w in wards]
    except Exception as e:
        logger.error(f"Error getting wards: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve wards")

@router.post("/ward", summary="Create a new ward")
def create_ward(
    ward_name: str = Body(..., embed=True, description="Ward (congregation) name"),
    db: Session = Depends(get_database_session)
) -> dict:
    """Create a new ward in the database."""
    try:
        existing = db.query(Ward).filter(Ward.name == ward_name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ward already exists")
        ward = Ward(name=ward_name)
        db.add(ward)
        db.commit()
        db.refresh(ward)
        return {"message": f"Ward '{ward_name}' created.", "id": ward.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ward: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create ward")

@router.get("/ward/{ward_name}", summary="Get ward details")
def get_ward(ward_name: str, db: Session = Depends(get_database_session)) -> dict:
    """Get details for a specific ward from the database."""
    try:
        ward = db.query(Ward).filter(Ward.name == ward_name).first()
        if not ward:
            raise HTTPException(status_code=404, detail="Ward not found")
        return {"id": ward.id, "ward_name": ward.name, "created_at": ward.created_at}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ward: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ward")

@router.put("/ward/{ward_name}", summary="Update ward name")
def update_ward(
    ward_name: str,
    new_name: str = Body(..., embed=True, description="New ward name"),
    db: Session = Depends(get_database_session)
) -> dict:
    """Update the name of a ward in the database."""
    try:
        ward = db.query(Ward).filter(Ward.name == ward_name).first()
        if not ward:
            raise HTTPException(status_code=404, detail="Ward not found")
        if db.query(Ward).filter(Ward.name == new_name).first():
            raise HTTPException(status_code=400, detail="New ward name already exists")
        ward.name = new_name  # type: ignore[assignment]
        db.commit()
        db.refresh(ward)
        return {"message": f"Ward '{ward_name}' renamed to '{new_name}'."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ward: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update ward")

@router.delete("/ward/{ward_name}", summary="Delete a ward")
def delete_ward(ward_name: str, db: Session = Depends(get_database_session)) -> dict:
    """Delete a ward from the database."""
    try:
        ward = db.query(Ward).filter(Ward.name == ward_name).first()
        if not ward:
            raise HTTPException(status_code=404, detail="Ward not found")
        db.delete(ward)
        db.commit()
        return {"message": f"Ward '{ward_name}' deleted."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ward: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete ward")

# --- Ward History Operations ---

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


@router.delete("/ward_history/{ward_name}", summary="Delete a hymn selection from ward history")
def delete_ward_selection(
    ward_name: str,
    selection_date: str = Query(..., description="Selection date in YYYY-MM-DD format"),
    history_service: HymnHistoryService = Depends(get_history_service)
) -> dict:
    """Delete a specific hymn selection from a ward's history."""
    try:
        from datetime import datetime

        # Parse the date
        try:
            parsed_date = datetime.strptime(selection_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Delete the selection
        deleted = history_service.delete_selection(ward_name, parsed_date)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Selection not found")
        
        return {"message": f"Selection for {ward_name} on {selection_date} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ward selection: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete selection")
