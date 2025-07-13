"""Pytest tests for the Italian Hymns API."""

import pytest
import requests
from fastapi.testclient import TestClient
from hymns.service import HymnService
from lds_tools import app

# Create test client
client = TestClient(app)


class TestAPI:
    """Test class for API endpoints."""

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Italian Hymns API"

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Italian Hymns API"

    def test_stats_endpoint(self):
        """Test the stats endpoint."""
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_hymns" in data
        assert "categories" in data
        assert "tags" in data
        assert "sacramento_hymns" in data
        assert isinstance(data["total_hymns"], int)
        assert data["total_hymns"] > 0

    def test_categories_endpoint(self):
        """Test the categories endpoint."""
        response = client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "sacramento" in [cat.lower() for cat in data]

    def test_tags_endpoint(self):
        """Test the tags endpoint."""
        response = client.get("/api/v1/tags")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_hymns_default(self):
        """Test getting hymns with default parameters."""
        response = client.get("/api/v1/get_hymns")
        assert response.status_code == 200
        data = response.json()
        assert "hymns" in data
        assert "count" in data
        assert data["count"] == 4  # Default is 4 hymns
        assert len(data["hymns"]) == 4

    def test_get_hymns_prima_domenica(self):
        """Test getting hymns for first Sunday."""
        response = client.get("/api/v1/get_hymns?prima_domenica=true")
        assert response.status_code == 200
        data = response.json()
        assert "hymns" in data
        assert "count" in data
        assert data["count"] == 3  # First Sunday is 3 hymns
        assert len(data["hymns"]) == 3

    def test_get_hymns_festive(self):
        """Test getting hymns for festive Sunday."""
        response = client.get("/api/v1/get_hymns?domenica_festiva=true&tipo_festivita=natale")
        assert response.status_code == 200
        data = response.json()
        assert "hymns" in data
        assert "count" in data
        assert data["count"] == 4

    def test_get_hymns_festive_missing_type(self):
        """Test that festive Sunday requires tipo_festivita."""
        response = client.get("/api/v1/get_hymns?domenica_festiva=true")
        assert response.status_code == 400

    def test_get_hymn_by_number(self):
        """Test getting a hymn by number."""
        response = client.get("/api/v1/get_hymn?number=1")
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert "songNumber" in data
        assert data["songNumber"] == 1

    def test_get_hymn_by_category(self):
        """Test getting a hymn by category."""
        response = client.get("/api/v1/get_hymn?category=sacramento")
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert "bookSectionTitle" in data
        assert data["bookSectionTitle"].lower() == "sacramento"

    def test_get_hymn_by_tag(self):
        """Test getting a hymn by tag."""
        response = client.get("/api/v1/get_hymn?tag=natale")
        assert response.status_code == 200
        data = response.json()
        # Note: This might return None if no hymns have the natale tag
        if data is not None:
            assert "tags" in data
            assert "natale" in [tag.lower() for tag in data["tags"]]

    def test_get_hymn_no_match(self):
        """Test getting a hymn with no matches."""
        response = client.get("/api/v1/get_hymn?number=99999")
        assert response.status_code == 200
        data = response.json()
        assert data is None

    def test_sacramento_hymn_in_selection(self):
        """Test that Sacramento hymn is always second in selection."""
        response = client.get("/api/v1/get_hymns")
        assert response.status_code == 200
        data = response.json()
        hymns = data["hymns"]
        assert len(hymns) == 4
        # Second hymn (index 1) should be Sacramento
        assert hymns[1]["bookSectionTitle"].lower() == "sacramento"


class TestHymnService:
    """Test class for HymnService business logic."""

    @pytest.fixture
    def service(self):
        """Create a HymnService instance for testing."""
        return HymnService(data_path="data/italian_hymns_full.json")

    def test_service_initialization(self, service):
        """Test that service initializes correctly."""
        assert len(service.hymns) > 0

    def test_get_categories(self, service):
        """Test getting categories."""
        categories = service.get_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "sacramento" in [cat.lower() for cat in categories]

    def test_get_tags(self, service):
        """Test getting tags."""
        tags = service.get_tags()
        assert isinstance(tags, list)
        assert len(tags) > 0

    def test_get_stats(self, service):
        """Test getting statistics."""
        stats = service.get_stats()
        assert "total_hymns" in stats
        assert "categories" in stats
        assert "tags" in stats
        assert "sacramento_hymns" in stats
        assert stats["total_hymns"] > 0
        assert stats["sacramento_hymns"] > 0
