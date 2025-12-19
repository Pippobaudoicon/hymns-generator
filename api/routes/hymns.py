"""Hymn-related endpoints."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.dependencies import get_accessible_ward_ids, get_current_active_user
from auth.models import User, UserRole
from config.settings import settings
from database.database import get_database_session
from database.history_service import HymnHistoryService
from database.models import Ward
from hymns.exceptions import HymnAPIException
from hymns.models import FestivityType, Hymn, HymnFilter, HymnList
from hymns.service import HymnService
from utils.date_utils import get_next_sunday

logger = logging.getLogger(__name__)

router = APIRouter()


# Request model for swap endpoint
class SwapHymnRequest(BaseModel):
    """Request body for swapping a hymn."""
    position: int
    current_hymn_number: int
    ward_id: int = None
    ward_name: str = None
    domenica_festiva: bool = False
    tipo_festivita: Optional[str] = None
    new_hymn_number: Optional[int] = None  # If None, get a random one

# Service dependencies
def get_hymn_service() -> HymnService:
    """Dependency to get hymn service instance."""
    return HymnService(data_path=settings.get_data_path())

def get_history_service(hymn_service: HymnService = Depends(get_hymn_service)) -> HymnHistoryService:
    """Dependency to get hymn history service instance."""
    return HymnHistoryService(hymn_service)


async def verify_ward_access_for_hymns(
    ward_id: int = None,
    ward_name: str = None,
    current_user: User = None,
    db: Session = None
) -> Ward:
    """Verify user has access to the ward for hymn operations."""
    ward = None
    if ward_id:
        ward = db.query(Ward).filter(Ward.id == ward_id).first()
    elif ward_name:
        ward = db.query(Ward).filter(Ward.name == ward_name).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    user_role = UserRole(current_user.role)
    if user_role != UserRole.SUPERADMIN:
        accessible_ids = await get_accessible_ward_ids(current_user, db)
        if accessible_ids is not None and ward.id not in accessible_ids:
            raise HTTPException(status_code=403, detail="You don't have access to this ward")
    
    return ward


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
async def get_hymns_smart(
    ward_id: int = Query(None, description="Ward ID (preferred)"),
    ward_name: str = Query(None, description="Ward (congregation) name (fallback)"),
    prima_domenica: bool = Query(False, description="First Sunday of month (3 hymns instead of 4)"),
    domenica_festiva: bool = Query(False, description="Festive Sunday"),
    tipo_festivita: Optional[FestivityType] = Query(None, description="Type of festivity (required if domenica_festiva=true)"),
    save_selection: bool = Query(True, description="Save this selection to database"),
    selection_date: Optional[str] = Query(None, description="Selection date (YYYY-MM-DD format, defaults to today)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
    history_service: HymnHistoryService = Depends(get_history_service)
) -> HymnList:
    """
    Generate a smart list of hymns that avoids repetition within 5 weeks.
    
    This endpoint tracks hymn usage by ward and ensures the same hymns
    aren't repeated within a 5-Sunday window.
    """
    try:
        # Verify ward access (prefer id)
        await verify_ward_access_for_hymns(ward_id=ward_id, ward_name=ward_name, current_user=current_user, db=db)
        
        # Parse selection date if provided, otherwise use next Sunday
        if selection_date:
            try:
                parsed_date = datetime.strptime(selection_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            # Default to next Sunday if no date provided
            parsed_date = get_next_sunday()
        
        # Get smart hymn selection
        hymns = history_service.get_smart_hymns(
            ward_id=ward_id,
            ward_name=ward_name,
            prima_domenica=prima_domenica,
            domenica_festiva=domenica_festiva,
            tipo_festivita=tipo_festivita,
            selection_date=parsed_date
        )
        
        # Save selection if requested
        if save_selection:
            history_service.save_selection(
                ward_id=ward_id,
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


@router.get("/get_replacement_hymn", response_model=Hymn, summary="Get a replacement hymn for a specific position")
async def get_replacement_hymn(
    position: int = Query(..., ge=1, le=4, description="Position of the hymn to replace (1-4)"),
    ward_id: int = Query(None, description="Ward ID (preferred)"),
    ward_name: str = Query(None, description="Ward name (fallback)"),
    prima_domenica: bool = Query(False, description="First Sunday of month"),
    domenica_festiva: bool = Query(False, description="Festive Sunday"),
    tipo_festivita: Optional[FestivityType] = Query(None, description="Type of festivity"),
    exclude_numbers: str = Query("", description="Comma-separated hymn numbers to exclude"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
    history_service: HymnHistoryService = Depends(get_history_service)
) -> Hymn:
    """
    Get a single replacement hymn for a specific position.
    Position 2 will always return a Sacramento hymn.
    Excludes hymns specified in exclude_numbers to avoid duplicates.
    """
    try:
        # Verify ward access (prefer id)
        await verify_ward_access_for_hymns(ward_id=ward_id, ward_name=ward_name, current_user=current_user, db=db)
        
        # Parse excluded hymn numbers
        excluded = set()
        if exclude_numbers:
            excluded = {int(n.strip()) for n in exclude_numbers.split(",") if n.strip().isdigit()}
        
        # Get replacement hymn
        hymn = history_service.get_replacement_hymn(
            position=position,
            ward_id=ward_id,
            ward_name=ward_name,
            prima_domenica=prima_domenica,
            domenica_festiva=domenica_festiva,
            tipo_festivita=tipo_festivita,
            exclude_numbers=excluded
        )
        
        return hymn
        
    except HymnAPIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_replacement_hymn: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/get_available_hymns", response_model=HymnList, summary="Get list of available hymns for a position")
async def get_available_hymns(
    position: int = Query(..., ge=1, le=4, description="Position of the hymn (1-4)"),
    ward_id: int = Query(None, description="Ward ID (preferred)"),
    ward_name: str = Query(None, description="Ward name (fallback)"),
    prima_domenica: bool = Query(False, description="First Sunday of month"),
    domenica_festiva: bool = Query(False, description="Festive Sunday"),
    tipo_festivita: Optional[FestivityType] = Query(None, description="Type of festivity"),
    exclude_numbers: str = Query("", description="Comma-separated hymn numbers to exclude"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
    history_service: HymnHistoryService = Depends(get_history_service)
) -> HymnList:
    """
    Get all available hymns that can be used for a specific position.
    Position 2 will return only Sacramento hymns.
    Excludes hymns used in the last 5 weeks and those specified in exclude_numbers.
    """
    try:
        # Verify ward access (prefer id)
        await verify_ward_access_for_hymns(ward_id=ward_id, ward_name=ward_name, current_user=current_user, db=db)
        
        # Parse excluded hymn numbers
        excluded = set()
        if exclude_numbers:
            excluded = {int(n.strip()) for n in exclude_numbers.split(",") if n.strip().isdigit()}
        
        # Get available hymns
        hymns = history_service.get_available_hymns(
            position=position,
            ward_id=ward_id,
            ward_name=ward_name,
            prima_domenica=prima_domenica,
            domenica_festiva=domenica_festiva,
            tipo_festivita=tipo_festivita,
            exclude_numbers=excluded
        )
        
        return HymnList(hymns=hymns)
        
    except HymnAPIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_available_hymns: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/swap_hymn", response_model=Hymn, summary="Swap a hymn in the current selection")
async def swap_hymn(
    request: SwapHymnRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
    history_service: HymnHistoryService = Depends(get_history_service)
) -> Hymn:
    """
    Swap a single hymn in the current selection.
    Updates both the returned hymn and the database record.
    
    If new_hymn_number is provided, get that specific hymn.
    If new_hymn_number is None, get a random replacement hymn.
    """
    try:
        # Verify ward access (prefer id)
        await verify_ward_access_for_hymns(ward_id=request.ward_id, ward_name=request.ward_name, current_user=current_user, db=db)
        
        # Parse festivita type if provided
        tipo_festivita = None
        if request.tipo_festivita:
            try:
                tipo_festivita = FestivityType(request.tipo_festivita)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid tipo_festivita: {request.tipo_festivita}")
        
        if request.new_hymn_number:
            # Get specific hymn
            hymn_service = history_service.hymn_service
            hymn = hymn_service.get_hymn_by_number(request.new_hymn_number)
            if not hymn:
                raise HTTPException(status_code=404, detail=f"Hymn {request.new_hymn_number} not found")
        else:
            # Get random replacement
            hymn = history_service.get_replacement_hymn(
                position=request.position,
                ward_id=request.ward_id,
                ward_name=request.ward_name,
                domenica_festiva=request.domenica_festiva,
                tipo_festivita=tipo_festivita,
                exclude_numbers={request.current_hymn_number}
            )
        
        # Update the database with the new hymn
        history_service.update_hymn_in_selection(
            ward_id=request.ward_id,
            ward_name=request.ward_name,
            position=request.position,
            new_hymn=hymn
        )
        
        return hymn
            
    except HymnAPIException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in swap_hymn: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
