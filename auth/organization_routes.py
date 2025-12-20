"""Organization management routes (Areas and Stakes)."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_database_session
from database.models import HymnSelection, SelectedHymn, Ward

from .dependencies import get_current_active_user, require_role
from .models import Area, Stake, User, UserRole
from .schemas import AreaCreate, AreaResponse, AreaUpdate, StakeCreate, StakeResponse, StakeUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Area Endpoints ---


@router.get("/areas", response_model=List[AreaResponse], summary="List all areas")
def list_areas(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
) -> List[AreaResponse]:
    """List all areas. All authenticated users can see areas."""
    areas = db.query(Area).order_by(Area.name).all()
    return [
        AreaResponse(
            id=a.id, name=a.name, created_at=a.created_at, stake_count=len(a.stakes)
        )
        for a in areas
    ]


@router.post("/areas", response_model=AreaResponse, summary="Create a new area")
def create_area(
    area_data: AreaCreate,
    current_user: User = Depends(require_role([UserRole.SUPERADMIN])),
    db: Session = Depends(get_database_session),
) -> AreaResponse:
    """Create a new area. Only superadmin can create areas."""
    try:
        # Check if area already exists
        if db.query(Area).filter(Area.name == area_data.name).first():
            raise HTTPException(status_code=400, detail="Area already exists")

        area = Area(name=area_data.name)
        db.add(area)
        db.commit()
        db.refresh(area)

        return AreaResponse(
            id=area.id, name=area.name, created_at=area.created_at, stake_count=0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating area: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create area")


@router.get("/areas/{area_id}", response_model=AreaResponse, summary="Get area by ID")
def get_area(
    area_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
) -> AreaResponse:
    """Get a specific area by ID."""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")

    return AreaResponse(
        id=area.id,
        name=area.name,
        created_at=area.created_at,
        stake_count=len(area.stakes),
    )


@router.put("/areas/{area_id}", response_model=AreaResponse, summary="Update an area")
def update_area(
    area_id: int,
    area_data: AreaUpdate,
    current_user: User = Depends(require_role([UserRole.SUPERADMIN])),
    db: Session = Depends(get_database_session),
) -> AreaResponse:
    """Update an area. Only superadmin can update areas."""
    try:
        area = db.query(Area).filter(Area.id == area_id).first()
        if not area:
            raise HTTPException(status_code=404, detail="Area not found")

        if area_data.name:
            existing = (
                db.query(Area)
                .filter(Area.name == area_data.name, Area.id != area_id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="Area name already exists")
            area.name = area_data.name

        db.commit()
        db.refresh(area)

        return AreaResponse(
            id=area.id,
            name=area.name,
            created_at=area.created_at,
            stake_count=len(area.stakes),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating area: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update area")


@router.delete("/areas/{area_id}", summary="Delete an area")
def delete_area(
    area_id: int,
    current_user: User = Depends(require_role([UserRole.SUPERADMIN])),
    db: Session = Depends(get_database_session),
) -> dict:
    """Delete an area. Only superadmin can delete areas."""
    try:
        area = db.query(Area).filter(Area.id == area_id).first()
        if not area:
            raise HTTPException(status_code=404, detail="Area not found")

        db.delete(area)
        db.commit()

        return {"message": f"Area '{area.name}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting area: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete area")


# --- Stake Endpoints ---


@router.get("/stakes", response_model=List[StakeResponse], summary="List all stakes")
def list_stakes(
    area_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
) -> List[StakeResponse]:
    """
    List all stakes, optionally filtered by area.
    - Superadmin sees all stakes
    - Area manager sees stakes in their area
    - Others see stakes they have access to
    """
    user_role = UserRole(current_user.role)

    query = db.query(Stake)

    if area_id:
        query = query.filter(Stake.area_id == area_id)
    elif user_role == UserRole.AREA_MANAGER and current_user.area_id:
        query = query.filter(Stake.area_id == current_user.area_id)

    stakes = query.order_by(Stake.name).all()

    return [
        StakeResponse(
            id=s.id,
            name=s.name,
            area_id=s.area_id,
            area_name=s.area.name if s.area else None,
            created_at=s.created_at,
            ward_count=len(s.wards),
        )
        for s in stakes
    ]


@router.post("/stakes", response_model=StakeResponse, summary="Create a new stake")
def create_stake(
    stake_data: StakeCreate,
    current_user: User = Depends(
        require_role([UserRole.SUPERADMIN, UserRole.AREA_MANAGER])
    ),
    db: Session = Depends(get_database_session),
) -> StakeResponse:
    """
    Create a new stake.
    - Superadmin can create stakes in any area
    - Area manager can only create stakes in their area
    """
    try:
        user_role = UserRole(current_user.role)

        # Validate area access
        if stake_data.area_id:
            area = db.query(Area).filter(Area.id == stake_data.area_id).first()
            if not area:
                raise HTTPException(status_code=404, detail="Area not found")

            if (
                user_role == UserRole.AREA_MANAGER
                and current_user.area_id != stake_data.area_id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="You can only create stakes in your assigned area",
                )
        elif user_role == UserRole.AREA_MANAGER:
            # Default to user's area
            stake_data.area_id = current_user.area_id

        # Check if stake already exists
        if db.query(Stake).filter(Stake.name == stake_data.name).first():
            raise HTTPException(status_code=400, detail="Stake already exists")

        stake = Stake(name=stake_data.name, area_id=stake_data.area_id)
        db.add(stake)
        db.commit()
        db.refresh(stake)

        return StakeResponse(
            id=stake.id,
            name=stake.name,
            area_id=stake.area_id,
            area_name=stake.area.name if stake.area else None,
            created_at=stake.created_at,
            ward_count=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating stake: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create stake")


@router.get(
    "/stakes/{stake_id}", response_model=StakeResponse, summary="Get stake by ID"
)
def get_stake(
    stake_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
) -> StakeResponse:
    """Get a specific stake by ID."""
    stake = db.query(Stake).filter(Stake.id == stake_id).first()
    if not stake:
        raise HTTPException(status_code=404, detail="Stake not found")

    return StakeResponse(
        id=stake.id,
        name=stake.name,
        area_id=stake.area_id,
        area_name=stake.area.name if stake.area else None,
        created_at=stake.created_at,
        ward_count=len(stake.wards),
    )


@router.put(
    "/stakes/{stake_id}", response_model=StakeResponse, summary="Update a stake"
)
def update_stake(
    stake_id: int,
    stake_data: StakeUpdate,
    current_user: User = Depends(
        require_role([UserRole.SUPERADMIN, UserRole.AREA_MANAGER])
    ),
    db: Session = Depends(get_database_session),
) -> StakeResponse:
    """
    Update a stake.
    - Superadmin can update any stake
    - Area manager can only update stakes in their area
    """
    try:
        stake = db.query(Stake).filter(Stake.id == stake_id).first()
        if not stake:
            raise HTTPException(status_code=404, detail="Stake not found")

        user_role = UserRole(current_user.role)

        # Check access for area managers
        if user_role == UserRole.AREA_MANAGER:
            if stake.area_id != current_user.area_id:
                raise HTTPException(
                    status_code=403,
                    detail="You can only update stakes in your assigned area",
                )

        if stake_data.name:
            existing = (
                db.query(Stake)
                .filter(Stake.name == stake_data.name, Stake.id != stake_id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="Stake name already exists")
            stake.name = stake_data.name

        if stake_data.area_id is not None:
            if stake_data.area_id:
                area = db.query(Area).filter(Area.id == stake_data.area_id).first()
                if not area:
                    raise HTTPException(status_code=404, detail="Area not found")
            stake.area_id = stake_data.area_id

        db.commit()
        db.refresh(stake)

        return StakeResponse(
            id=stake.id,
            name=stake.name,
            area_id=stake.area_id,
            area_name=stake.area.name if stake.area else None,
            created_at=stake.created_at,
            ward_count=len(stake.wards),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating stake: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update stake")


@router.delete("/stakes/{stake_id}", summary="Delete a stake")
def delete_stake(
    stake_id: int,
    current_user: User = Depends(
        require_role([UserRole.SUPERADMIN, UserRole.AREA_MANAGER])
    ),
    db: Session = Depends(get_database_session),
) -> dict:
    """
    Delete a stake.
    - Superadmin can delete any stake
    - Area manager can only delete stakes in their area
    """
    try:
        stake = db.query(Stake).filter(Stake.id == stake_id).first()
        if not stake:
            raise HTTPException(status_code=404, detail="Stake not found")

        user_role = UserRole(current_user.role)

        # Check access for area managers
        if user_role == UserRole.AREA_MANAGER:
            if stake.area_id != current_user.area_id:
                raise HTTPException(
                    status_code=403,
                    detail="You can only delete stakes in your assigned area",
                )

        stake_name = stake.name

        # Manually delete related hymn data for all wards in this stake
        for ward in stake.wards:
            # Delete selected hymns for each hymn selection
            for selection in ward.hymn_selections:
                db.query(SelectedHymn).filter(
                    SelectedHymn.selection_id == selection.id
                ).delete()
            # Delete hymn selections
            db.query(HymnSelection).filter(HymnSelection.ward_id == ward.id).delete()
        # Delete wards in the stake
        db.query(Ward).filter(Ward.stake_id == stake_id).delete()

        db.delete(stake)
        db.commit()

        return {"message": f"Stake '{stake_name}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting stake: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete stake")


# --- Stakes within Area ---


@router.get(
    "/areas/{area_id}/stakes",
    response_model=List[StakeResponse],
    summary="Get stakes in an area",
)
def get_area_stakes(
    area_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
) -> List[StakeResponse]:
    """Get all stakes in a specific area."""
    area = db.query(Area).filter(Area.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")

    return [
        StakeResponse(
            id=s.id,
            name=s.name,
            area_id=s.area_id,
            area_name=area.name,
            created_at=s.created_at,
            ward_count=len(s.wards),
        )
        for s in area.stakes
    ]


# --- Wards within Stake ---


@router.get("/stakes/{stake_id}/wards", summary="Get wards in a stake")
def get_stake_wards(
    stake_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
) -> List[dict]:
    """Get all wards in a specific stake."""
    stake = db.query(Stake).filter(Stake.id == stake_id).first()
    if not stake:
        raise HTTPException(status_code=404, detail="Stake not found")

    return [
        {
            "id": w.id,
            "name": w.name,
            "stake_id": stake_id,
            "stake_name": stake.name,
            "created_at": w.created_at,
        }
        for w in stake.wards
    ]


# --- Ward Endpoints ---


@router.get("/wards", summary="List all wards")
def list_wards(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
) -> List[dict]:
    """List all wards. All authenticated users can see wards."""
    wards = db.query(Ward).order_by(Ward.name).all()
    return [
        {"id": w.id, "name": w.name, "stake_id": w.stake_id, "created_at": w.created_at}
        for w in wards
    ]


@router.post("/wards", summary="Create a new ward")
def create_ward(
    ward_data: dict,
    current_user: User = Depends(
        require_role(
            [UserRole.SUPERADMIN, UserRole.AREA_MANAGER, UserRole.STAKE_MANAGER]
        )
    ),
    db: Session = Depends(get_database_session),
) -> dict:
    """Create a new ward. Requires stake_manager or higher role."""
    name = ward_data.get("name")
    stake_id = ward_data.get("stake_id")

    if not name or not stake_id:
        raise HTTPException(status_code=400, detail="Name and stake_id are required")

    # Verify stake exists
    stake = db.query(Stake).filter(Stake.id == stake_id).first()
    if not stake:
        raise HTTPException(status_code=404, detail="Stake not found")

    # Check if ward name already exists
    existing = db.query(Ward).filter(Ward.name == name).first()
    if existing:
        raise HTTPException(
            status_code=400, detail="Ward with this name already exists"
        )

    ward = Ward(name=name, stake_id=stake_id)
    db.add(ward)
    db.commit()
    db.refresh(ward)

    logger.info(f"Ward '{name}' created by {current_user.username}")

    return {
        "id": ward.id,
        "name": ward.name,
        "stake_id": ward.stake_id,
        "created_at": ward.created_at,
    }


@router.put("/wards/{ward_id}", summary="Update a ward")
def update_ward(
    ward_id: int,
    ward_data: dict,
    current_user: User = Depends(
        require_role(
            [UserRole.SUPERADMIN, UserRole.AREA_MANAGER, UserRole.STAKE_MANAGER]
        )
    ),
    db: Session = Depends(get_database_session),
) -> dict:
    """Update a ward. Requires stake_manager or higher role."""
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")

    if "name" in ward_data and ward_data["name"]:
        # Check for duplicate name
        existing = (
            db.query(Ward)
            .filter(Ward.name == ward_data["name"], Ward.id != ward_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400, detail="Ward with this name already exists"
            )
        ward.name = ward_data["name"]

    if "stake_id" in ward_data and ward_data["stake_id"]:
        stake = db.query(Stake).filter(Stake.id == ward_data["stake_id"]).first()
        if not stake:
            raise HTTPException(status_code=404, detail="Stake not found")
        ward.stake_id = ward_data["stake_id"]

    db.commit()
    db.refresh(ward)

    logger.info(f"Ward '{ward.name}' updated by {current_user.username}")

    return {
        "id": ward.id,
        "name": ward.name,
        "stake_id": ward.stake_id,
        "created_at": ward.created_at,
    }


@router.delete("/wards/{ward_id}", summary="Delete a ward")
def delete_ward(
    ward_id: int,
    current_user: User = Depends(
        require_role(
            [UserRole.SUPERADMIN, UserRole.AREA_MANAGER, UserRole.STAKE_MANAGER]
        )
    ),
    db: Session = Depends(get_database_session),
) -> dict:
    """Delete a ward. Requires stake_manager or higher role."""
    try:
        ward = db.query(Ward).filter(Ward.id == ward_id).first()
        if not ward:
            raise HTTPException(status_code=404, detail="Ward not found")

        ward_name = ward.name

        # Manually delete related hymn data (SQLite doesn't cascade properly)
        for selection in ward.hymn_selections:
            db.query(SelectedHymn).filter(
                SelectedHymn.selection_id == selection.id
            ).delete()
        db.query(HymnSelection).filter(HymnSelection.ward_id == ward_id).delete()

        db.delete(ward)
        db.commit()

        logger.info(f"Ward '{ward_name}' deleted by {current_user.username}")

        return {"message": f"Ward '{ward_name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ward: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete ward")
