"""Pydantic schemas for authentication."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from .models import UserRole

# --- Token Schemas ---


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data encoded in JWT token."""

    username: Optional[str] = None


# --- User Schemas ---


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.WARD_USER
    area_id: Optional[int] = None  # For area managers
    stake_id: Optional[int] = None  # For stake managers
    ward_ids: Optional[List[int]] = None  # For ward users


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    area_id: Optional[int] = None
    stake_id: Optional[int] = None
    ward_ids: Optional[List[int]] = None


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    role: UserRole
    is_active: bool
    area_id: Optional[int] = None
    stake_id: Optional[int] = None
    assigned_ward_ids: List[int] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


# --- Area Schemas ---


class AreaBase(BaseModel):
    """Base area schema."""

    name: str = Field(..., min_length=1, max_length=255)


class AreaCreate(AreaBase):
    """Schema for creating an area."""

    pass


class AreaUpdate(BaseModel):
    """Schema for updating an area."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)


class AreaResponse(AreaBase):
    """Schema for area response."""

    id: int
    created_at: datetime
    stake_count: int = 0

    class Config:
        from_attributes = True


# --- Stake Schemas ---


class StakeBase(BaseModel):
    """Base stake schema."""

    name: str = Field(..., min_length=1, max_length=255)
    area_id: Optional[int] = None


class StakeCreate(StakeBase):
    """Schema for creating a stake."""

    pass


class StakeUpdate(BaseModel):
    """Schema for updating a stake."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    area_id: Optional[int] = None


class StakeResponse(StakeBase):
    """Schema for stake response."""

    id: int
    area_name: Optional[str] = None
    created_at: datetime
    ward_count: int = 0

    class Config:
        from_attributes = True


# --- Ward Assignment Schemas ---


class WardAssignment(BaseModel):
    """Schema for assigning wards to a user."""

    user_id: int
    ward_ids: List[int]


class UserWardResponse(BaseModel):
    """Response showing user's ward assignments."""

    user_id: int
    username: str
    wards: List[dict]  # List of {id, name}
