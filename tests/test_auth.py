"""Pytest tests for authentication and admin functionality."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import app
from auth.models import UserRole
from auth.utils import get_password_hash
from database.database import get_database_session
from database.models import Base, User

# Create test client
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def override_get_db(test_db):
    """Override the database dependency."""
    def _override_get_db():
        yield test_db
    app.dependency_overrides[get_database_session] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def test_superadmin(test_db):
    """Create a test superadmin user."""
    user = User(
        username="superadmin",
        email="superadmin@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Super Admin",
        role=UserRole.SUPERADMIN,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_area_manager(test_db):
    """Create a test area manager user."""
    user = User(
        username="area_manager",
        email="area_manager@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Area Manager",
        role=UserRole.AREA_MANAGER,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_success(self, override_get_db, test_superadmin):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            data={"username": "superadmin", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, override_get_db, test_superadmin):
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/login",
            data={"username": "superadmin", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, override_get_db):
        """Test login with non-existent user."""
        response = client.post(
            "/auth/login",
            data={"username": "nonexistent", "password": "password123"}
        )
        assert response.status_code == 401


class TestUserManagement:
    """Test user management endpoints."""

    def test_get_current_user(self, override_get_db, test_superadmin):
        """Test getting current user info."""
        # First login to get token
        login_response = client.post(
            "/auth/login",
            data={"username": "superadmin", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "superadmin"
        assert data["role"] == "superadmin"

    def test_get_users_unauthorized(self, override_get_db):
        """Test getting users without authentication."""
        response = client.get("/auth/users")
        assert response.status_code == 403  # Forbidden without auth

    def test_get_users_as_superadmin(self, override_get_db, test_superadmin, test_area_manager):
        """Test superadmin can get all users."""
        # Login as superadmin
        login_response = client.post(
            "/auth/login",
            data={"username": "superadmin", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        
        # Get users
        response = client.get(
            "/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least superadmin and area_manager


class TestUserRole:
    """Test user role functionality."""

    def test_superadmin_role(self, test_superadmin):
        """Test superadmin role is set correctly."""
        assert test_superadmin.role == UserRole.SUPERADMIN

    def test_area_manager_role(self, test_area_manager):
        """Test area manager role is set correctly."""
        assert test_area_manager.role == UserRole.AREA_MANAGER

    def test_user_active_status(self, test_superadmin):
        """Test user active status."""
        assert test_superadmin.is_active is True


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_password_hash_verification(self, test_superadmin):
        """Test that password is properly hashed."""
        from auth.utils import verify_password

        # Verify correct password
        assert verify_password("password123", test_superadmin.hashed_password)
        
        # Verify incorrect password
        assert not verify_password("wrongpassword", test_superadmin.hashed_password)

    def test_password_hash_different_for_same_input(self):
        """Test that hashing the same password produces different hashes."""
        hash1 = get_password_hash("password123")
        hash2 = get_password_hash("password123")
        # Hashes should be different (bcrypt uses salt)
        assert hash1 != hash2
