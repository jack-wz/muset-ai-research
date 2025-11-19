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


@pytest.mark.asyncio
async def test_edit_file_lines_single_edit(file_system_manager: FileSystemManager):
    """Test editing single line."""
    from app.services.file_system_manager import Edit

    path = "test_lines.txt"
    initial_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"

    # Create file
    await file_system_manager.write_file(path, initial_content)

    # Edit line 3
    edits = [Edit(start_line=3, end_line=3, new_content="Modified Line 3")]
    await file_system_manager.edit_file_lines(path, edits)

    # Verify
    content = await file_system_manager.read_file(path)
    assert content == "Line 1\nLine 2\nModified Line 3\nLine 4\nLine 5"


@pytest.mark.asyncio
async def test_edit_file_lines_multiple_edits(file_system_manager: FileSystemManager):
    """Test editing multiple lines."""
    from app.services.file_system_manager import Edit

    path = "test_multiple.txt"
    initial_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"

    # Create file
    await file_system_manager.write_file(path, initial_content)

    # Edit multiple lines
    edits = [
        Edit(start_line=2, end_line=3, new_content="New Line 2\nNew Line 3"),
        Edit(start_line=5, end_line=5, new_content="New Line 5"),
    ]
    await file_system_manager.edit_file_lines(path, edits)

    # Verify
    content = await file_system_manager.read_file(path)
    assert content == "Line 1\nNew Line 2\nNew Line 3\nLine 4\nNew Line 5"


@pytest.mark.asyncio
async def test_edit_file_lines_invalid_range(file_system_manager: FileSystemManager):
    """Test that invalid line ranges raise errors."""
    from app.services.file_system_manager import Edit

    path = "test_invalid.txt"
    await file_system_manager.write_file(path, "Line 1\nLine 2\nLine 3")

    # Test invalid range (start > end)
    with pytest.raises(ValueError, match="Invalid edit range"):
        edits = [Edit(start_line=3, end_line=2, new_content="Invalid")]
        await file_system_manager.edit_file_lines(path, edits)

    # Test out of bounds
    with pytest.raises(ValueError, match="exceeds file length"):
        edits = [Edit(start_line=1, end_line=10, new_content="Invalid")]
        await file_system_manager.edit_file_lines(path, edits)


@pytest.mark.asyncio
async def test_edit_file_lines_overlapping_edits(file_system_manager: FileSystemManager):
    """Test that overlapping edits raise errors."""
    from app.services.file_system_manager import Edit

    path = "test_overlap.txt"
    await file_system_manager.write_file(path, "Line 1\nLine 2\nLine 3\nLine 4\nLine 5")

    # Test overlapping edits
    with pytest.raises(ValueError, match="Overlapping edits"):
        edits = [
            Edit(start_line=2, end_line=4, new_content="Edit 1"),
            Edit(start_line=3, end_line=5, new_content="Edit 2"),  # Overlaps with first
        ]
        await file_system_manager.edit_file_lines(path, edits)
