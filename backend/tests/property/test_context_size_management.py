"""Property test: Context size management.

Verifies requirement 2.2.
"""
import tempfile

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

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


# Property 3: Context size management
@settings(max_examples=50)
@given(
    # Generate content that exceeds the threshold
    content_size=st.integers(
        min_value=FileSystemManager.CONTEXT_THRESHOLD + 1,
        max_value=FileSystemManager.CONTEXT_THRESHOLD * 3,
    ),
)
@pytest.mark.asyncio
async def test_large_content_externalization(
    file_system_manager: FileSystemManager,
    content_size: int,
):
    """
    Test that large content is identified for externalization.

    This property verifies:
    - Content exceeding threshold is detected (Req 2.2)
    - System can handle large content appropriately
    """
    # Generate large content
    content = "a" * content_size

    # Check if content should be externalized
    should_externalize = await file_system_manager.should_externalize_content(content)

    assert should_externalize, f"Content of size {content_size} should be externalized"


@settings(max_examples=50)
@given(
    # Generate content below threshold
    content_size=st.integers(
        min_value=1,
        max_value=FileSystemManager.CONTEXT_THRESHOLD,
    ),
)
@pytest.mark.asyncio
async def test_small_content_not_externalized(
    file_system_manager: FileSystemManager,
    content_size: int,
):
    """Test that small content is not externalized."""
    content = "a" * content_size

    should_externalize = await file_system_manager.should_externalize_content(content)

    assert not should_externalize, f"Content of size {content_size} should not be externalized"


@pytest.mark.asyncio
async def test_large_content_written_to_file(
    file_system_manager: FileSystemManager,
):
    """Test that large content can be written to and read from file."""
    # Generate content larger than threshold
    large_content = "x" * (FileSystemManager.CONTEXT_THRESHOLD + 1000)

    path = "test/large_file.txt"

    # Write large content
    file_record = await file_system_manager.write_file(path, large_content)

    # Verify file was created
    assert file_record is not None
    assert file_record.size > FileSystemManager.CONTEXT_THRESHOLD

    # Read content back
    read_content = await file_system_manager.read_file(path)

    # Verify content is preserved
    assert read_content == large_content
    assert len(read_content) > FileSystemManager.CONTEXT_THRESHOLD


@settings(max_examples=20)
@given(
    num_chunks=st.integers(min_value=2, max_value=10),
)
@pytest.mark.asyncio
async def test_incremental_content_growth(
    file_system_manager: FileSystemManager,
    num_chunks: int,
):
    """Test content that grows incrementally beyond threshold."""
    chunk_size = FileSystemManager.CONTEXT_THRESHOLD // 2
    path = "test/growing_file.txt"

    content = ""
    for i in range(num_chunks):
        chunk = f"Chunk {i}: " + ("x" * chunk_size)
        content += chunk

        await file_system_manager.write_file(path, content)

        # Check if should be externalized
        should_externalize = await file_system_manager.should_externalize_content(content)

        if len(content) > FileSystemManager.CONTEXT_THRESHOLD:
            assert should_externalize, f"Content should be externalized after {i+1} chunks"
        else:
            assert not should_externalize, f"Content should not be externalized after {i+1} chunks"

        # Verify content is preserved
        read_content = await file_system_manager.read_file(path)
        assert read_content == content
