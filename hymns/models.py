"""Data models for the Italian Hymns API."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FestivityType(str, Enum):
    """Available festivity types."""

    NATALE = "natale"
    PASQUA = "pasqua"


class HymnCategory(str, Enum):
    """Common hymn categories."""

    SACRAMENTO = "sacramento"
    OCCASIONI_SPECIALI = "occasioni speciali"
    RESTAURAZIONE = "restaurazione"
    SECONDA_VENUTA = "seconda venuta"
    VANGELO = "vangelo"
    # Add more as needed


class Hymn(BaseModel):
    """Represents a single hymn."""

    number: int = Field(alias="songNumber", description="Hymn number")
    title: str = Field(description="Hymn title")
    category: str = Field(alias="bookSectionTitle", description="Hymn category")
    tags: List[str] = Field(default_factory=list, description="Hymn tags")
    slug: Optional[str] = Field(None, description="URL slug")
    audio_url: Optional[str] = Field(None, description="Audio accompaniment URL")
    composers: List[str] = Field(default_factory=list, description="Composers")
    authors: List[str] = Field(default_factory=list, description="Authors")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        """Parse tags if they come as a string."""
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(",") if tag.strip()]
        return v or []

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v):
        """Normalize category to lowercase."""
        return v.lower().strip() if v else ""


class HymnList(BaseModel):
    """Represents a list of hymns."""

    hymns: List[Hymn] = Field(description="List of hymns")
    count: int = Field(description="Number of hymns")

    def __init__(self, hymns: List[Hymn], **data):
        super().__init__(hymns=hymns, count=len(hymns), **data)


class PaginatedHymnList(BaseModel):
    """Represents a paginated list of hymns."""

    hymns: List[Hymn] = Field(description="List of hymns")
    total: int = Field(description="Total number of hymns matching filters")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of hymns per page")
    total_pages: int = Field(description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hymns": [],
                "total": 100,
                "page": 1,
                "page_size": 50,
                "total_pages": 2,
            }
        }
    )


class HymnFilter(BaseModel):
    """Filter criteria for hymn selection."""

    number: Optional[int] = Field(None, description="Specific hymn number")
    category: Optional[str] = Field(None, description="Hymn category")
    tag: Optional[str] = Field(None, description="Hymn tag")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"number": 1, "category": "sacramento", "tag": "natale"}
        }
    )


class HymnSelectionRequest(BaseModel):
    """Request model for hymn selection."""

    prima_domenica: bool = Field(
        False, description="First Sunday of month (3 hymns instead of 4)"
    )
    domenica_festiva: bool = Field(False, description="Festive Sunday")
    tipo_festivita: Optional[FestivityType] = Field(
        None, description="Type of festivity"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prima_domenica": False,
                "domenica_festiva": True,
                "tipo_festivita": "natale",
            }
        }
    )
