"""RAG API routes for LDS content Q&A, search, and generation."""

import hashlib
import logging
import time
from collections import defaultdict
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth.dependencies import get_current_active_user
from auth.models import User
from rag.pipeline import RAGPipeline
from rag.schemas import Language, RAGQuery, RAGResult, SearchResult, SourceType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG"])

# ---------------------------------------------------------------------------
# Rate limiting (simple in-memory, per-user)
# ---------------------------------------------------------------------------

_rate_limits: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 10  # max requests per window for expensive endpoints


def _check_rate_limit(user_id: str, max_requests: int = RATE_LIMIT_MAX_REQUESTS):
    """Raise 429 if user exceeds rate limit."""
    now = time.time()
    timestamps = _rate_limits[user_id]

    # Remove expired entries
    _rate_limits[user_id] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]

    if len(_rate_limits[user_id]) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {max_requests} requests per {RATE_LIMIT_WINDOW}s.",
        )

    _rate_limits[user_id].append(now)


# ---------------------------------------------------------------------------
# Pipeline singleton
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _get_pipeline() -> RAGPipeline:
    """Get or create the RAG pipeline singleton."""
    return RAGPipeline()


# ---------------------------------------------------------------------------
# Response caching
# ---------------------------------------------------------------------------

_response_cache: dict[str, RAGResult] = {}
MAX_CACHE_SIZE = 200


def _cache_key(query: str, lang: str, sources: tuple[str, ...], top_k: int) -> str:
    raw = f"{query}|{lang}|{','.join(sources)}|{top_k}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/query", response_model=RAGResult)
async def rag_query(
    query: RAGQuery,
    user: User = Depends(get_current_active_user),
):
    """Full RAG Q&A: retrieve relevant chunks and generate an answer."""
    _check_rate_limit(str(user.id))

    # Check cache
    cache_key = _cache_key(
        query.question, query.language.value, tuple(s.value for s in query.sources), query.top_k
    )
    if cache_key in _response_cache:
        logger.info(f"Cache hit for query: {query.question[:50]}")
        return _response_cache[cache_key]

    pipeline = _get_pipeline()
    result = pipeline.ask_from_query(query)

    # Cache result
    if len(_response_cache) < MAX_CACHE_SIZE:
        _response_cache[cache_key] = result

    return result


@router.get("/search", response_model=SearchResult)
async def rag_search(
    q: str = Query(min_length=3, max_length=500, description="Search query"),
    source: Optional[SourceType] = Query(None, description="Filter by source"),
    lang: Language = Query(Language.ITA, description="Language"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results"),
    user: User = Depends(get_current_active_user),
):
    """Semantic search across LDS sources (no LLM generation)."""
    sources = [source] if source else list(SourceType)

    pipeline = _get_pipeline()
    return pipeline.search(
        query=q,
        language=lang,
        sources=sources,
        top_k=top_k,
    )


class GenerateRequest(RAGQuery):
    """Request for content generation (talk outline, lesson plan, etc.)."""

    pass


@router.post("/generate", response_model=RAGResult)
async def rag_generate(
    request: GenerateRequest,
    user: User = Depends(get_current_active_user),
):
    """Generate content (talk outline, lesson plan, etc.) grounded in LDS sources."""
    _check_rate_limit(str(user.id))

    pipeline = _get_pipeline()
    return pipeline.ask_from_query(request)


@router.get("/sources")
async def rag_sources(
    user: User = Depends(get_current_active_user),
):
    """List available source collections and their chunk counts."""
    from rag.vector_store import VectorStore

    try:
        store = VectorStore()
        namespaces = store.list_namespaces()
    except Exception as e:
        logger.error(f"Failed to get source stats: {e}")
        namespaces = {}

    return {
        "sources": [
            {
                "name": st.value,
                "label": st.value.replace("-", " ").title(),
                "chunks": namespaces.get(st.value, 0),
            }
            for st in SourceType
        ],
        "total_chunks": sum(namespaces.values()),
    }
