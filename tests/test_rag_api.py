"""Tests for RAG API routes."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.schemas import Language, RAGResult, SearchResult, SourceChunk, SourceType


@pytest.fixture
def mock_pipeline():
    """Mock the RAG pipeline for API tests."""
    mock = MagicMock()

    mock_chunks = [
        SourceChunk(
            id="c1",
            text="La fede è la certezza delle cose sperate...",
            source=SourceType.SCRIPTURES,
            score=0.95,
            book="Alma",
            chapter=32,
            verse="21",
        )
    ]

    mock.ask_from_query.return_value = RAGResult(
        query="Cos'è la fede?",
        answer="La fede è la certezza delle cose che si sperano...",
        sources=mock_chunks,
        language=Language.ITA,
        model="claude-haiku-4-5-20241022",
    )

    mock.search.return_value = SearchResult(
        query="fede",
        chunks=mock_chunks,
        language=Language.ITA,
    )

    return mock


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.is_active = True
    user.role = "superadmin"
    return user


@pytest.fixture
def authed_client(client, mock_user, mock_pipeline):
    """Test client with mocked auth and pipeline."""
    from api.routes import rag as rag_module
    from auth.dependencies import get_current_active_user

    # Override auth
    from app import app

    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    # Override pipeline
    with patch.object(rag_module, "_get_pipeline", return_value=mock_pipeline):
        # Clear rate limit state between tests
        rag_module._rate_limits.clear()
        rag_module._response_cache.clear()
        yield client

    app.dependency_overrides.pop(get_current_active_user, None)


class TestRAGQuery:
    """Test POST /api/v1/rag/query."""

    def test_query_success(self, authed_client, mock_pipeline):
        resp = authed_client.post(
            "/api/v1/rag/query",
            json={"question": "Cos'è la fede?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert data["query"] == "Cos'è la fede?"
        assert len(data["sources"]) > 0
        mock_pipeline.ask_from_query.assert_called_once()

    def test_query_with_options(self, authed_client):
        resp = authed_client.post(
            "/api/v1/rag/query",
            json={
                "question": "What is faith?",
                "language": "eng",
                "sources": ["scriptures"],
                "top_k": 3,
            },
        )
        assert resp.status_code == 200

    def test_query_validation_short(self, authed_client):
        resp = authed_client.post(
            "/api/v1/rag/query",
            json={"question": "ab"},
        )
        assert resp.status_code == 422

    def test_query_requires_auth(self, client):
        resp = client.post(
            "/api/v1/rag/query",
            json={"question": "Cos'è la fede?"},
        )
        assert resp.status_code in (401, 403)


class TestRAGSearch:
    """Test GET /api/v1/rag/search."""

    def test_search_success(self, authed_client, mock_pipeline):
        resp = authed_client.get("/api/v1/rag/search?q=fede")
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "fede"
        assert len(data["chunks"]) > 0
        mock_pipeline.search.assert_called_once()

    def test_search_with_filters(self, authed_client):
        resp = authed_client.get(
            "/api/v1/rag/search?q=pentimento&source=conference&lang=ita&top_k=3"
        )
        assert resp.status_code == 200

    def test_search_validation(self, authed_client):
        resp = authed_client.get("/api/v1/rag/search?q=ab")
        assert resp.status_code == 422

    def test_search_requires_auth(self, client):
        resp = client.get("/api/v1/rag/search?q=fede")
        assert resp.status_code in (401, 403)


class TestRAGGenerate:
    """Test POST /api/v1/rag/generate."""

    def test_generate_success(self, authed_client, mock_pipeline):
        resp = authed_client.post(
            "/api/v1/rag/generate",
            json={"question": "Prepara una lezione sulla fede"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data

    def test_generate_requires_auth(self, client):
        resp = client.post(
            "/api/v1/rag/generate",
            json={"question": "Prepara una lezione sulla fede"},
        )
        assert resp.status_code in (401, 403)


class TestRAGSources:
    """Test GET /api/v1/rag/sources."""

    def test_sources_success(self, authed_client):
        with patch("rag.vector_store.Pinecone") as MockPinecone:
            mock_index = MagicMock()
            mock_index.describe_index_stats.return_value = {
                "namespaces": {
                    "scriptures": {"vector_count": 30000},
                    "conference": {"vector_count": 15000},
                }
            }
            MockPinecone.return_value.Index.return_value = mock_index

            resp = authed_client.get("/api/v1/rag/sources")
            assert resp.status_code == 200
            data = resp.json()
            assert "sources" in data
            assert "total_chunks" in data
            assert len(data["sources"]) == len(SourceType)

    def test_sources_requires_auth(self, client):
        resp = client.get("/api/v1/rag/sources")
        assert resp.status_code in (401, 403)


class TestRateLimit:
    """Test rate limiting on expensive endpoints."""

    def test_rate_limit_enforced(self, authed_client, mock_pipeline):
        from api.routes import rag as rag_module

        rag_module._rate_limits.clear()

        # Make requests up to the limit
        for i in range(10):
            resp = authed_client.post(
                "/api/v1/rag/query",
                json={"question": f"Question number {i} about faith"},
            )
            assert resp.status_code == 200

        # Next request should be rate limited
        resp = authed_client.post(
            "/api/v1/rag/query",
            json={"question": "One more question about faith"},
        )
        assert resp.status_code == 429
