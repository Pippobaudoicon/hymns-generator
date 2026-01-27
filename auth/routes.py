"""Authentication routes."""

import logging
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database.database import get_database_session
from database.models import Ward

from .dependencies import get_current_active_user, require_role
from .models import Stake, User, UserRole
from .schemas import Token, UserCreate, UserResponse, UserUpdate, UserWardResponse
from .utils import create_access_token, get_password_hash, verify_password

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Authentication Endpoints ---


@router.post("/login", response_model=Token, summary="Login to get access token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_database_session),
) -> Token:
    """
    Authenticate user and return JWT access token.

    Accepts form data with username and password fields.
    """
    form_data.username = form_data.username.lower()
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse, summary="Get current user")
def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Get information about the currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=UserRole(current_user.role),
        is_active=current_user.is_active,
        area_id=current_user.area_id,
        stake_id=current_user.stake_id,
        assigned_ward_ids=[w.id for w in current_user.assigned_wards],
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.put("/me", response_model=UserResponse, summary="Update current user profile")
def update_current_user(
    email: str = Body(None),
    full_name: str = Body(None),
    current_password: str = Body(None),
    new_password: str = Body(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database_session),
) -> UserResponse:
    """Update current user's profile (email, full_name, password)."""
    try:
        if email:
            # Check if email is already taken
            existing = (
                db.query(User)
                .filter(User.email == email, User.id != current_user.id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
            current_user.email = email

        if full_name is not None:
            current_user.full_name = full_name

        if new_password:
            if not current_password:
                raise HTTPException(
                    status_code=400,
                    detail="Current password required to set new password",
                )
            if not verify_password(current_password, current_user.hashed_password):
                raise HTTPException(
                    status_code=400, detail="Current password is incorrect"
                )
            current_user.hashed_password = get_password_hash(new_password)

        db.commit()
        db.refresh(current_user)

        return UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            role=UserRole(current_user.role),
            is_active=current_user.is_active,
            area_id=current_user.area_id,
            stake_id=current_user.stake_id,
            assigned_ward_ids=[w.id for w in current_user.assigned_wards],
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update profile")


# --- User Management Endpoints (Admin Only) ---


@router.get("/users", response_model=List[UserResponse], summary="List all users")
def list_users(
    current_user: User = Depends(
        require_role(
            [UserRole.SUPERADMIN, UserRole.AREA_MANAGER, UserRole.STAKE_MANAGER]
        )
    ),
    db: Session = Depends(get_database_session),
) -> List[UserResponse]:
    """
    List all users.
    - Superadmin sees all users
    - Area manager sees users in their area
    - Stake manager sees users in their stake
    """
    user_role = UserRole(current_user.role)

    if user_role == UserRole.SUPERADMIN:
        users = db.query(User).all()
    elif user_role == UserRole.AREA_MANAGER and current_user.area_id:
        # Get users who manage stakes in this area, or have wards in this area
        stake_ids = [
            s.id
            for s in db.query(Stake).filter(Stake.area_id == current_user.area_id).all()
        ]
        ward_ids = [
            w.id for w in db.query(Ward).filter(Ward.stake_id.in_(stake_ids)).all()
        ]

        users = (
            db.query(User)
            .filter(
                (User.area_id == current_user.area_id)
                | (User.stake_id.in_(stake_ids))
                | (User.assigned_wards.any(Ward.id.in_(ward_ids)))
            )
            .all()
        )
    elif user_role == UserRole.STAKE_MANAGER and current_user.stake_id:
        # Get users who have wards in this stake
        ward_ids = [
            w.id
            for w in db.query(Ward).filter(Ward.stake_id == current_user.stake_id).all()
        ]

        users = (
            db.query(User)
            .filter(
                (User.stake_id == current_user.stake_id)
                | (User.assigned_wards.any(Ward.id.in_(ward_ids)))
            )
            .all()
        )
    else:
        users = []

    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            role=UserRole(u.role),
            is_active=u.is_active,
            area_id=u.area_id,
            stake_id=u.stake_id,
            assigned_ward_ids=[w.id for w in u.assigned_wards],
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in users
    ]


@router.post("/users", response_model=UserResponse, summary="Create a new user")
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(
        require_role(
            [UserRole.SUPERADMIN, UserRole.AREA_MANAGER, UserRole.STAKE_MANAGER]
        )
    ),
    db: Session = Depends(get_database_session),
) -> UserResponse:
    """
    Create a new user. Only admins can create users.
    - Superadmin can create any user
    - Area manager can create stake managers and ward users in their area
    - Stake manager can create ward users in their stake
    """
    try:
        current_role = UserRole(current_user.role)

        # Validate permissions based on who's creating
        if current_role == UserRole.AREA_MANAGER:
            if user_data.role in [UserRole.SUPERADMIN, UserRole.AREA_MANAGER]:
                raise HTTPException(
                    status_code=403,
                    detail="Area managers cannot create superadmins or other area managers",
                )
        elif current_role == UserRole.STAKE_MANAGER:
            if user_data.role != UserRole.WARD_USER:
                raise HTTPException(
                    status_code=403, detail="Stake managers can only create ward users"
                )

        # Check if username or email already exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(status_code=400, detail="Username already registered")
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role.value,
            area_id=(
                user_data.area_id if user_data.role == UserRole.AREA_MANAGER else None
            ),
            stake_id=(
                user_data.stake_id if user_data.role == UserRole.STAKE_MANAGER else None
            ),
        )

        db.add(new_user)
        db.flush()  # Get the ID

        # Assign wards if provided
        if user_data.ward_ids and user_data.role == UserRole.WARD_USER:
            wards = db.query(Ward).filter(Ward.id.in_(user_data.ward_ids)).all()
            new_user.assigned_wards = wards

        db.commit()
        db.refresh(new_user)

        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            role=UserRole(new_user.role),
            is_active=new_user.is_active,
            area_id=new_user.area_id,
            stake_id=new_user.stake_id,
            assigned_ward_ids=[w.id for w in new_user.assigned_wards],
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.get("/users/{user_id}", response_model=UserResponse, summary="Get user by ID")
def get_user(
    user_id: int,
    current_user: User = Depends(
        require_role(
            [UserRole.SUPERADMIN, UserRole.AREA_MANAGER, UserRole.STAKE_MANAGER]
        )
    ),
    db: Session = Depends(get_database_session),
) -> UserResponse:
    """Get a specific user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=UserRole(user.role),
        is_active=user.is_active,
        area_id=user.area_id,
        stake_id=user.stake_id,
        assigned_ward_ids=[w.id for w in user.assigned_wards],
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.put("/users/{user_id}", response_model=UserResponse, summary="Update a user")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(
        require_role(
            [UserRole.SUPERADMIN, UserRole.AREA_MANAGER, UserRole.STAKE_MANAGER]
        )
    ),
    db: Session = Depends(get_database_session),
) -> UserResponse:
    """Update a user. Admins can update user details and assignments."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update fields if provided
        if user_data.email:
            existing = (
                db.query(User)
                .filter(User.email == user_data.email, User.id != user_id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
            user.email = user_data.email

        if user_data.full_name is not None:
            user.full_name = user_data.full_name

        if user_data.password:
            user.hashed_password = get_password_hash(user_data.password)

        if user_data.role and UserRole(current_user.role) == UserRole.SUPERADMIN:
            user.role = user_data.role.value

        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        if user_data.area_id is not None:
            user.area_id = user_data.area_id

        if user_data.stake_id is not None:
            user.stake_id = user_data.stake_id

        if user_data.ward_ids is not None:
            wards = db.query(Ward).filter(Ward.id.in_(user_data.ward_ids)).all()
            user.assigned_wards = wards

        db.commit()
        db.refresh(user)

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=UserRole(user.role),
            is_active=user.is_active,
            area_id=user.area_id,
            stake_id=user.stake_id,
            assigned_ward_ids=[w.id for w in user.assigned_wards],
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update user")


@router.delete("/users/{user_id}", summary="Delete a user")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.SUPERADMIN])),
    db: Session = Depends(get_database_session),
) -> dict:
    """Delete a user. Only superadmin can delete users."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")

        db.delete(user)
        db.commit()

        return {"message": f"User '{user.username}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete user")


# --- Ward Assignment Endpoints ---


@router.post(
    "/users/{user_id}/wards",
    response_model=UserWardResponse,
    summary="Assign wards to user",
)
@router.put(
    "/users/{user_id}/wards",
    response_model=UserWardResponse,
    summary="Assign wards to user",
)
def assign_wards_to_user(
    user_id: int,
    ward_ids: List[int] = Body(..., embed=True),
    current_user: User = Depends(
        require_role(
            [UserRole.SUPERADMIN, UserRole.AREA_MANAGER, UserRole.STAKE_MANAGER]
        )
    ),
    db: Session = Depends(get_database_session),
) -> UserWardResponse:
    """Assign wards to a user. Replaces existing assignments."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        wards = db.query(Ward).filter(Ward.id.in_(ward_ids)).all()
        if len(wards) != len(ward_ids):
            raise HTTPException(status_code=400, detail="Some ward IDs are invalid")

        user.assigned_wards = wards
        db.commit()
        db.refresh(user)

        return UserWardResponse(
            user_id=user.id,
            username=user.username,
            wards=[{"id": w.id, "name": w.name} for w in user.assigned_wards],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning wards: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to assign wards")


@router.get(
    "/users/{user_id}/wards",
    response_model=UserWardResponse,
    summary="Get user's ward assignments",
)
def get_user_wards(
    user_id: int,
    current_user: User = Depends(
        require_role(
            [UserRole.SUPERADMIN, UserRole.AREA_MANAGER, UserRole.STAKE_MANAGER]
        )
    ),
    db: Session = Depends(get_database_session),
) -> UserWardResponse:
    """Get wards assigned to a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserWardResponse(
        user_id=user.id,
        username=user.username,
        wards=[{"id": w.id, "name": w.name} for w in user.assigned_wards],
    )
