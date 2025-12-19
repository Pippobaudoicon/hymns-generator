"""FastAPI dependencies for authentication and authorization."""

import logging
from functools import wraps
from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database.database import get_database_session
from database.models import Ward

from .models import Area, Stake, User, UserRole
from .utils import decode_access_token

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify they are active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(required_roles: List[UserRole]):
    """
    Dependency factory that requires user to have one of the specified roles.
    
    Usage:
        @router.get("/admin-only")
        def admin_endpoint(user: User = Depends(require_role([UserRole.SUPERADMIN]))):
            ...
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        user_role = UserRole(current_user.role)
        
        # Superadmin can access everything
        if user_role == UserRole.SUPERADMIN:
            return current_user
        
        # Check if user has one of the required roles
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in required_roles]}"
            )
        
        return current_user
    
    return role_checker


async def get_accessible_ward_ids(
    user: User,
    db: Session
) -> Optional[List[int]]:
    """
    Get list of ward IDs the user can access.
    Returns None if user can access all wards (superadmin).
    """
    user_role = UserRole(user.role)
    
    if user_role == UserRole.SUPERADMIN:
        return None  # Can access all
    
    if user_role == UserRole.AREA_MANAGER and user.area_id:
        # Get all wards in stakes belonging to user's area
        stakes = db.query(Stake).filter(Stake.area_id == user.area_id).all()
        stake_ids = [s.id for s in stakes]
        wards = db.query(Ward).filter(Ward.stake_id.in_(stake_ids)).all()
        return [w.id for w in wards]
    
    if user_role == UserRole.STAKE_MANAGER and user.stake_id:
        # Get all wards in user's stake
        wards = db.query(Ward).filter(Ward.stake_id == user.stake_id).all()
        return [w.id for w in wards]
    
    # Ward user - only assigned wards
    return [w.id for w in user.assigned_wards]


def require_ward_access(ward_id_param: str = "ward_id", ward_name_param: str = "ward_name"):
    """
    Dependency factory that requires user to have access to the specified ward.
    
    The ward can be identified by either ward_id or ward_name parameter.
    
    Usage:
        @router.get("/ward/{ward_id}/hymns")
        def get_ward_hymns(
            ward_id: int,
            user: User = Depends(require_ward_access(ward_id_param="ward_id"))
        ):
            ...
    """
    async def ward_access_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_database_session),
        **kwargs
    ) -> User:
        user_role = UserRole(current_user.role)
        
        # Superadmin can access everything
        if user_role == UserRole.SUPERADMIN:
            return current_user
        
        # Get ward ID from parameters
        ward_id = kwargs.get(ward_id_param)
        ward_name = kwargs.get(ward_name_param)
        
        ward = None
        if ward_id:
            ward = db.query(Ward).filter(Ward.id == ward_id).first()
        elif ward_name:
            ward = db.query(Ward).filter(Ward.name == ward_name).first()
        
        if not ward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ward not found"
            )
        
        # Get accessible ward IDs for user
        accessible_ward_ids = await get_accessible_ward_ids(current_user, db)
        
        if accessible_ward_ids is not None and ward.id not in accessible_ward_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this ward"
            )
        
        return current_user
    
    return ward_access_checker


class WardAccessChecker:
    """
    Callable dependency class for checking ward access.
    
    Usage:
        @router.get("/ward/{ward_name}/hymns")
        def get_ward_hymns(
            ward_name: str,
            user: User = Depends(WardAccessChecker())
        ):
            ...
    """
    
    async def __call__(
        self,
        ward_name: str = None,
        ward_id: int = None,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_database_session),
    ) -> User:
        user_role = UserRole(current_user.role)
        
        # Superadmin can access everything
        if user_role == UserRole.SUPERADMIN:
            return current_user
        
        # Get ward
        ward = None
        if ward_id:
            ward = db.query(Ward).filter(Ward.id == ward_id).first()
        elif ward_name:
            ward = db.query(Ward).filter(Ward.name == ward_name).first()
        
        if not ward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ward not found"
            )
        
        # Get accessible ward IDs for user
        accessible_ward_ids = await get_accessible_ward_ids(current_user, db)
        
        if accessible_ward_ids is not None and ward.id not in accessible_ward_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this ward"
            )
        
        return current_user


# Convenient dependency instances
check_ward_access = WardAccessChecker()
