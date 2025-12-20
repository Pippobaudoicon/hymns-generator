"""Database models for hymn selection history."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Ward(Base):
    """Represents a ward (congregation)."""

    __tablename__ = "wards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    stake_id = Column(
        Integer, ForeignKey("stakes.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to stake
    stake = relationship("Stake", back_populates="wards")

    # Relationship to hymn selections
    hymn_selections = relationship(
        "HymnSelection", back_populates="ward", cascade="all, delete-orphan"
    )

    # Many-to-many relationship with users
    assigned_users = relationship(
        "User", secondary="user_ward_assignments", back_populates="assigned_wards"
    )


class HymnSelection(Base):
    """Represents a set of hymns selected for a particular Sunday."""

    __tablename__ = "hymn_selections"

    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    selection_date = Column(DateTime, nullable=False, index=True)
    prima_domenica = Column(Boolean, default=False)
    domenica_festiva = Column(Boolean, default=False)
    tipo_festivita = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to ward and hymns
    ward = relationship("Ward", back_populates="hymn_selections")
    hymns = relationship(
        "SelectedHymn", back_populates="selection", cascade="all, delete-orphan"
    )


class SelectedHymn(Base):
    """Represents an individual hymn in a selection."""

    __tablename__ = "selected_hymns"

    id = Column(Integer, primary_key=True, index=True)
    selection_id = Column(
        Integer, ForeignKey("hymn_selections.id", ondelete="CASCADE"), nullable=False
    )
    hymn_number = Column(Integer, nullable=False, index=True)
    hymn_title = Column(String(255), nullable=False)
    hymn_category = Column(String(100), nullable=False)
    position = Column(Integer, nullable=False)  # 1st, 2nd, 3rd, 4th hymn

    # Relationship to selection
    selection = relationship("HymnSelection", back_populates="hymns")
