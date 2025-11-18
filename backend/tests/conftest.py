"""Pytest configuration and fixtures."""
import tempfile

import pytest
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.db.base import Base

# Create a test base compatible with SQLite
TestBase = declarative_base()


# Simplified models for testing (SQLite compatible)
class TestContextFile(TestBase):
    """Test context file model."""

    __tablename__ = "context_files"

    id = Column(String, primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    workspace_id = Column(String, nullable=False)
    category = Column(String, nullable=False)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    checksum = Column(String, nullable=False)
    related_pages = Column(JSON, default=[])
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class TestFileVersion(TestBase):
    """Test file version model."""

    __tablename__ = "file_versions"

    id = Column(String, primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    file_id = Column(String, ForeignKey("context_files.id"), nullable=False)
    snapshot_path = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    diff_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class TestWritingPlan(TestBase):
    """Test writing plan model."""

    __tablename__ = "writing_plans"

    id = Column(String, primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    workspace_id = Column(String, nullable=False)
    page_id = Column(String, nullable=True)
    goal = Column(Text, nullable=False)
    source_prompt = Column(Text, nullable=False)
    status = Column(String, default="pending")
    current_task_id = Column(String, nullable=True)
    task_ids = Column(JSON, default=[])
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class TestTodoTask(TestBase):
    """Test todo task model."""

    __tablename__ = "todo_tasks"

    id = Column(String, primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    plan_id = Column(String, ForeignKey("writing_plans.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="pending")
    step_type = Column(String, nullable=False)
    priority = Column(String, default="medium")
    dependencies = Column(JSON, default=[])
    outputs = Column(JSON, default=[])
    assigned_agent_id = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class TestMemory(TestBase):
    """Test memory model."""

    __tablename__ = "memories"

    id = Column(String, primary_key=True, default=lambda: str(__import__("uuid").uuid4()))
    workspace_id = Column(String, nullable=False)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    embedding_id = Column(String, nullable=True)
    tags = Column(JSON, default=[])
    importance_score = Column(Integer, default=0.5)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


# Patch models to use test models
import app.models.file as file_module
import app.models.memory as memory_module
import app.models.task as task_module

file_module.ContextFile = TestContextFile
file_module.FileVersion = TestFileVersion
task_module.WritingPlan = TestWritingPlan
task_module.TodoTask = TestTodoTask
memory_module.Memory = TestMemory


@pytest.fixture(scope="session")
def engine():
    """Create test database engine.

    Note: This uses an in-memory SQLite database for testing.
    In production, you would use a test PostgreSQL database.
    """
    # Use SQLite for testing (in-memory)
    engine = create_engine("sqlite:///:memory:")
    TestBase.metadata.create_all(bind=engine)
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


@pytest.fixture
async def test_db():
    """Create an async test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def file_system_manager(test_db):
    """Create a file system manager for testing."""
    from app.services.file_system_manager import FileSystemManager

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = FileSystemManager(
            workspace_id="test-workspace",
            base_path=tmpdir,
            session=test_db,
        )
        yield manager
