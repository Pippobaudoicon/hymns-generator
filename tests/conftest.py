"""Pytest configuration and fixtures for Italian Hymns API tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app
from database.models import Base
from database.database import get_database_session
from hymns.service import HymnService
from config.settings import settings


@pytest.fixture(scope="session")
def test_data_path():
    """Provide path to test data file."""
    return str(Path(__file__).parent.parent / "data" / "italian_hymns_full.json")


@pytest.fixture(scope="session")
def hymn_service(test_data_path):
    """Create a HymnService instance for testing."""
    return HymnService(data_path=test_data_path)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database."""
    # Use in-memory SQLite for tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Provide session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with test database."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_database_session] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_hymns():
    """Provide sample hymn data for testing."""
    return [
        {
            "number": 1,
            "title": "Test Hymn 1",
            "category": "Sacramento",
            "tags": []
        },
        {
            "number": 2,
            "title": "Test Hymn 2",
            "category": "Restaurazione",
            "tags": ["natale"]
        },
        {
            "number": 3,
            "title": "Test Hymn 3",
            "category": "Sacramento",
            "tags": []
        }
    ]


@pytest.fixture
def mock_ward_data():
    """Provide mock ward data for testing."""
    return {
        "name": "Test Ward",
        "selections": []
    }