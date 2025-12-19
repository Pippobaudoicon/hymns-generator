"""Authentication and authorization database models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from database.models import Base


class UserRole(str, Enum):
    """User role hierarchy."""
    SUPERADMIN = "superadmin"      # Can do everything
    AREA_MANAGER = "area_manager"  # Can manage stakes in their area
    STAKE_MANAGER = "stake_manager"  # Can manage wards in their stake
    WARD_USER = "ward_user"        # Can manage hymns for assigned wards


# Association table for User <-> Ward many-to-many relationship
user_ward_association = Table(
    "user_ward_assignments",
    Base.metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("ward_id", Integer, ForeignKey("wards.id", ondelete="CASCADE"), nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
)


class Area(Base):
    """Represents a geographic area (contains multiple stakes)."""
    __tablename__ = "areas"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stakes = relationship("Stake", back_populates="area", cascade="all, delete-orphan")
    managers = relationship("User", back_populates="managed_area", foreign_keys="User.area_id")


class Stake(Base):
    """Represents a stake (contains multiple wards)."""
    __tablename__ = "stakes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    area = relationship("Area", back_populates="stakes")
    wards = relationship("Ward", back_populates="stake", cascade="all, delete-orphan")
    managers = relationship("User", back_populates="managed_stake", foreign_keys="User.stake_id")


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default=UserRole.WARD_USER.value, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # For area managers: which area they manage
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="SET NULL"), nullable=True)
    
    # For stake managers: which stake they manage
    stake_id = Column(Integer, ForeignKey("stakes.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    managed_area = relationship("Area", back_populates="managers", foreign_keys=[area_id])
    managed_stake = relationship("Stake", back_populates="managers", foreign_keys=[stake_id])
    
    # Many-to-many relationship with wards (for ward users)
    assigned_wards = relationship(
        "Ward",
        secondary=user_ward_association,
        back_populates="assigned_users"
    )
    
    @property
    def role_enum(self) -> UserRole:
        """Get role as enum."""
        return UserRole(self.role)
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has at least the given role level."""
        role_hierarchy = {
            UserRole.SUPERADMIN: 4,
            UserRole.AREA_MANAGER: 3,
            UserRole.STAKE_MANAGER: 2,
            UserRole.WARD_USER: 1,
        }
        return role_hierarchy.get(self.role_enum, 0) >= role_hierarchy.get(role, 0)
    
    def can_access_ward(self, ward_id: int) -> bool:
        """Check if user can access a specific ward."""
        from database.models import Ward

        # Superadmin can access everything
        if self.role_enum == UserRole.SUPERADMIN:
            return True
        
        # Area manager can access all wards in their area's stakes
        if self.role_enum == UserRole.AREA_MANAGER and self.area_id:
            # Need to check via database session - handled in dependency
            return True  # Will be verified in dependency
        
        # Stake manager can access all wards in their stake
        if self.role_enum == UserRole.STAKE_MANAGER and self.stake_id:
            return True  # Will be verified in dependency
        
        # Ward user can only access assigned wards
        return any(ward.id == ward_id for ward in self.assigned_wards)


# We need to add the relationship to Ward model - this will be done via import
# The Ward model in database/models.py needs to be updated
