"""Pytest configuration and fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base


@pytest.fixture(scope="session")
def engine():
    """Create test database engine.

    Note: This uses an in-memory SQLite database for testing.
    In production, you would use a test PostgreSQL database.
    """
    # Use SQLite for testing (in-memory)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine) -> Session:
    """Create a new database session for a test.

    Args:
        engine: SQLAlchemy engine

    Yields:
        Database session
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    session.rollback()
    session.close()
