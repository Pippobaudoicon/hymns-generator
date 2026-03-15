"""Pydantic models for the RAG module."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Available source collections."""

    SCRIPTURES = "scriptures"
    CONFERENCE = "conference"
    HANDBOOK = "handbook"
    LIAHONA = "liahona"


class Language(str, Enum):
    """Supported languages."""

    ITA = "ita"
    ENG = "eng"


class SourceChunk(BaseModel):
    """A chunk of source content retrieved from the vector store."""

    id: str
    text: str
    source: SourceType
    score: float = Field(ge=0.0, le=1.0, description="Similarity score")
    language: Language = Language.ITA

    # Optional metadata depending on source type
    book: Optional[str] = None
    chapter: Optional[int] = None
    verse: Optional[str] = None
    speaker: Optional[str] = None
    title: Optional[str] = None
    date: Optional[str] = None
    section: Optional[str] = None
    url: Optional[str] = None


class RAGQuery(BaseModel):
    """Input query for the RAG pipeline."""

    question: str = Field(min_length=3, max_length=1000)
    language: Language = Language.ITA
    sources: list[SourceType] = Field(
        default_factory=lambda: list(SourceType),
        description="Sources to search in. Defaults to all.",
    )
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    """Result from semantic search (no LLM generation)."""

    query: str
    chunks: list[SourceChunk]
    language: Language


class RAGResult(BaseModel):
    """Full RAG result with generated answer and source citations."""

    query: str
    answer: str
    sources: list[SourceChunk]
    language: Language
    model: str = ""
