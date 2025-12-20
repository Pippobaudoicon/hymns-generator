"""Database setup and connection management."""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from config.settings import settings

from .models import Base


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str = None):
        """Initialize database manager."""
        if database_url is None:
            # Default to SQLite database in project root
            db_path = Path(settings.PROJECT_ROOT) / "data" / "hymns_history.db"
            db_path.parent.mkdir(exist_ok=True)
            database_url = f"sqlite:///{db_path}"

        # For SQLite, we need special configuration
        if database_url.startswith("sqlite"):
            self.engine = create_engine(
                database_url,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,  # Allow multiple threads
                },
                echo=settings.is_debug(),  # Log SQL in debug mode
            )
        else:
            self.engine = create_engine(database_url, echo=settings.is_debug())

        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def get_session_context(self):
        """Context manager for database sessions (alias for session_scope)."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database manager instance
db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager


def get_database_session() -> Generator[Session, None, None]:
    """Dependency to get database session for FastAPI."""
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


def init_database():
    """Initialize the database with tables."""
    # Import auth models to register them with Base
    from auth.models import Area, Stake, User, user_ward_association  # noqa: F401

    db_manager.create_tables()
