"""Ward management and history endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth.dependencies import get_accessible_ward_ids, get_current_active_user, require_role
from auth.models import Stake, User, UserRole
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

@router.get("/wards", response_model=List[dict], summary="Get all wards")
async def get_wards(
    stake_id: Optional[int] = Query(None, description="Filter by stake ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session)
) -> List[dict]:
    """Get list of all wards from the database. Users only see wards they have access to."""
    try:
        query = db.query(Ward)
        
        # Filter by stake if provided
        if stake_id:
            query = query.filter(Ward.stake_id == stake_id)
        
        # Get accessible ward IDs for the user
        user_role = UserRole(current_user.role)
        if user_role != UserRole.SUPERADMIN:
            accessible_ids = await get_accessible_ward_ids(current_user, db)
            if accessible_ids is not None:
                query = query.filter(Ward.id.in_(accessible_ids))
        
        wards = query.order_by(Ward.name).all()
        return [
            {
                "id": w.id,
                "name": w.name,
                "stake_id": w.stake_id,
                "stake_name": w.stake.name if w.stake else None,
                "created_at": w.created_at
            }
            for w in wards
        ]
    except Exception as e:
        logger.error(f"Error getting wards: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve wards")

@router.post("/ward", summary="Create a new ward")
def create_ward(
    ward_name: str = Body(..., embed=True, description="Ward (congregation) name"),
    stake_id: Optional[int] = Body(None, embed=True, description="Stake ID this ward belongs to"),
    current_user: User = Depends(require_role([UserRole.SUPERADMIN, UserRole.AREA_MANAGER, UserRole.STAKE_MANAGER])),
    db: Session = Depends(get_database_session)
) -> dict:
    """
    Create a new ward in the database.
    - Superadmin can create wards in any stake
    - Area manager can create wards in stakes within their area
    - Stake manager can only create wards in their stake
    """
    try:
        user_role = UserRole(current_user.role)
        
        # Validate stake access
        if stake_id:
            stake = db.query(Stake).filter(Stake.id == stake_id).first()
            if not stake:
                raise HTTPException(status_code=404, detail="Stake not found")
            
            if user_role == UserRole.AREA_MANAGER and stake.area_id != current_user.area_id:
                raise HTTPException(status_code=403, detail="You can only create wards in your area's stakes")
            
            if user_role == UserRole.STAKE_MANAGER and stake_id != current_user.stake_id:
                raise HTTPException(status_code=403, detail="You can only create wards in your stake")
        elif user_role == UserRole.STAKE_MANAGER:
            stake_id = current_user.stake_id
        
        existing = db.query(Ward).filter(Ward.name == ward_name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ward already exists")
        
        ward = Ward(name=ward_name, stake_id=stake_id)
        db.add(ward)
        db.commit()
        db.refresh(ward)
        return {
            "message": f"Ward '{ward_name}' created.",
            "id": ward.id,
            "stake_id": ward.stake_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ward: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create ward")

@router.get("/ward/{ward_name}", summary="Get ward details")
def get_ward(
    ward_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session)
) -> dict:
    """Get details for a specific ward from the database."""
    try:
        ward = db.query(Ward).filter(Ward.name == ward_name).first()
        if not ward:
            raise HTTPException(status_code=404, detail="Ward not found")
        return {
            "id": ward.id,
            "ward_name": ward.name,
            "stake_id": ward.stake_id,
            "stake_name": ward.stake.name if ward.stake else None,
            "created_at": ward.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ward: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ward")

@router.put("/ward/{ward_name}", summary="Update ward name")
def update_ward(
    ward_name: str,
    new_name: str = Body(None, embed=True, description="New ward name"),
    stake_id: Optional[int] = Body(None, embed=True, description="New stake ID"),
    current_user: User = Depends(require_role([UserRole.SUPERADMIN, UserRole.AREA_MANAGER, UserRole.STAKE_MANAGER])),
    db: Session = Depends(get_database_session)
) -> dict:
    """Update a ward in the database."""
    try:
        ward = db.query(Ward).filter(Ward.name == ward_name).first()
        if not ward:
            raise HTTPException(status_code=404, detail="Ward not found")
        
        # Check access based on role
        user_role = UserRole(current_user.role)
        if user_role == UserRole.STAKE_MANAGER:
            if ward.stake_id != current_user.stake_id:
                raise HTTPException(status_code=403, detail="You can only update wards in your stake")
        elif user_role == UserRole.AREA_MANAGER:
            if ward.stake and ward.stake.area_id != current_user.area_id:
                raise HTTPException(status_code=403, detail="You can only update wards in your area")
        
        if new_name:
            if db.query(Ward).filter(Ward.name == new_name, Ward.id != ward.id).first():
                raise HTTPException(status_code=400, detail="New ward name already exists")
            ward.name = new_name
        
        if stake_id is not None:
            if stake_id:
                stake = db.query(Stake).filter(Stake.id == stake_id).first()
                if not stake:
                    raise HTTPException(status_code=404, detail="Stake not found")
            ward.stake_id = stake_id
        
        db.commit()
        db.refresh(ward)
        return {"message": f"Ward updated successfully.", "id": ward.id, "name": ward.name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ward: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update ward")

@router.delete("/ward/{ward_name}", summary="Delete a ward")
def delete_ward(
    ward_name: str,
    current_user: User = Depends(require_role([UserRole.SUPERADMIN, UserRole.AREA_MANAGER, UserRole.STAKE_MANAGER])),
    db: Session = Depends(get_database_session)
) -> dict:
    """Delete a ward from the database."""
    try:
        ward = db.query(Ward).filter(Ward.name == ward_name).first()
        if not ward:
            raise HTTPException(status_code=404, detail="Ward not found")
        
        # Check access based on role
        user_role = UserRole(current_user.role)
        if user_role == UserRole.STAKE_MANAGER:
            if ward.stake_id != current_user.stake_id:
                raise HTTPException(status_code=403, detail="You can only delete wards in your stake")
        elif user_role == UserRole.AREA_MANAGER:
            if ward.stake and ward.stake.area_id != current_user.area_id:
                raise HTTPException(status_code=403, detail="You can only delete wards in your area")
        
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

async def verify_ward_access(
    ward_name: str,
    current_user: User,
    db: Session
) -> Ward:
    """Verify user has access to the ward and return the ward."""
    ward = db.query(Ward).filter(Ward.name == ward_name).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    user_role = UserRole(current_user.role)
    if user_role != UserRole.SUPERADMIN:
        accessible_ids = await get_accessible_ward_ids(current_user, db)
        if accessible_ids is not None and ward.id not in accessible_ids:
            raise HTTPException(status_code=403, detail="You don't have access to this ward")
    
    return ward

@router.get("/ward_history/{ward_name}", summary="Get hymn selection history for a ward")
async def get_ward_history(
    ward_name: str,
    limit: int = Query(10, ge=1, le=50, description="Number of recent selections to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
    history_service: HymnHistoryService = Depends(get_history_service)
) -> dict:
    """Get recent hymn selection history for a specific ward."""
    try:
        # Verify access
        await verify_ward_access(ward_name, current_user, db)
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ward history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ward history")


@router.delete("/ward_history/{ward_name}", summary="Delete a hymn selection from ward history")
async def delete_ward_selection(
    ward_name: str,
    selection_date: str = Query(..., description="Selection date in YYYY-MM-DD format"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
    history_service: HymnHistoryService = Depends(get_history_service)
) -> dict:
    """Delete a specific hymn selection from a ward's history."""
    try:
        from datetime import datetime

        # Verify access
        await verify_ward_access(ward_name, current_user, db)

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
