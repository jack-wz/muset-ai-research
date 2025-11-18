"""Unit tests for FileSystemManager."""
import tempfile

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import FileNotFoundError, PermissionDeniedError
from app.db.base import Base
from app.services.file_system_manager import FileSystemManager


@pytest.fixture
async def test_db():
    """Create a test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def file_system_manager(test_db):
    """Create a file system manager for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = FileSystemManager(
            workspace_id="test-workspace",
            base_path=tmpdir,
            session=test_db,
        )
        yield manager


@pytest.mark.asyncio
async def test_write_and_read_file(file_system_manager: FileSystemManager):
    """Test writing and reading a file."""
    content = "Hello, World!"
    path = "test.txt"

    # Write file
    file_record = await file_system_manager.write_file(path, content)
    assert file_record is not None
    assert file_record.name == "test.txt"

    # Read file
    read_content = await file_system_manager.read_file(path)
    assert read_content == content


@pytest.mark.asyncio
async def test_edit_file(file_system_manager: FileSystemManager):
    """Test editing a file."""
    initial_content = "Hello, World!"
    path = "test.txt"

    await file_system_manager.write_file(path, initial_content)

    # Edit file
    await file_system_manager.edit_file(path, "World", "Universe")

    # Verify edit
    content = await file_system_manager.read_file(path)
    assert content == "Hello, Universe!"


@pytest.mark.asyncio
async def test_ls_files(file_system_manager: FileSystemManager):
    """Test listing files."""
    # Create some files
    await file_system_manager.write_file("file1.txt", "Content 1")
    await file_system_manager.write_file("dir/file2.txt", "Content 2")

    # List all files
    files = await file_system_manager.ls()
    assert "file1.txt" in files
    assert "dir/file2.txt" in files


@pytest.mark.asyncio
async def test_grep_search(file_system_manager: FileSystemManager):
    """Test grep search."""
    await file_system_manager.write_file("file1.txt", "Hello World\nTest Line")
    await file_system_manager.write_file("file2.txt", "Another File\nHello Again")

    # Search for pattern
    matches = await file_system_manager.grep("hello")
    assert len(matches) == 2


@pytest.mark.asyncio
async def test_file_not_found_error(file_system_manager: FileSystemManager):
    """Test that reading non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        await file_system_manager.read_file("nonexistent.txt")


@pytest.mark.asyncio
async def test_invalid_path_error(file_system_manager: FileSystemManager):
    """Test that invalid paths raise error."""
    with pytest.raises(PermissionDeniedError):
        await file_system_manager.write_file("../../../etc/passwd", "malicious")


@pytest.mark.asyncio
async def test_file_versioning(file_system_manager: FileSystemManager):
    """Test file version management."""
    path = "versioned.txt"

    # Create initial version
    await file_system_manager.write_file(path, "Version 1")

    # Update file
    await file_system_manager.write_file(path, "Version 2")

    # Check versions
    versions = await file_system_manager.get_file_versions(path)
    assert len(versions) >= 2
