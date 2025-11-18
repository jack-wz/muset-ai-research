"""Property test: File system roundtrip consistency.

Verifies requirements 2.1, 2.3.
"""
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.services.file_system_manager import FileSystemManager


# Database setup for tests
@pytest.fixture
async def test_db():
    """Create a test database."""
    # Use in-memory SQLite for testing
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


# Property 2: File system roundtrip consistency
@settings(max_examples=100)
@given(
    content=st.text(
        alphabet=st.characters(
            blacklist_categories=("Cs",),  # Exclude surrogate characters
            blacklist_characters=("\x00",),  # Exclude null bytes
        ),
        min_size=1,
        max_size=10000,
    ),
    filename=st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"),  # Letters and numbers
        ),
        min_size=1,
        max_size=50,
    ).map(lambda s: f"{s}.txt"),
)
@pytest.mark.asyncio
async def test_file_roundtrip_consistency(
    file_system_manager: FileSystemManager,
    content: str,
    filename: str,
):
    """
    Test that content written to a file can be read back identically.

    This property verifies:
    - Write operation stores content correctly (Req 2.1)
    - Read operation retrieves content correctly (Req 2.3)
    - Content is preserved through roundtrip
    """
    # Write content
    path = f"test/{filename}"
    await file_system_manager.write_file(path, content)

    # Read content back
    read_content = await file_system_manager.read_file(path)

    # Verify content is identical
    assert read_content == content, "Content should be identical after roundtrip"


@settings(max_examples=50)
@given(
    content=st.text(min_size=1, max_size=5000),
    # Test various encodings and special characters
    special_content=st.one_of(
        st.just("Hello\nWorld\n"),  # Newlines
        st.just("Tab\tseparated\tvalues"),  # Tabs
        st.just("Unicode: 你好世界 🌍"),  # Unicode
        st.just('Quotes: "double" and \'single\''),  # Quotes
        st.just("Backslash: \\path\\to\\file"),  # Backslashes
    ),
)
@pytest.mark.asyncio
async def test_special_characters_roundtrip(
    file_system_manager: FileSystemManager,
    content: str,
    special_content: str,
):
    """Test roundtrip with special characters and encodings."""
    combined_content = content + "\n" + special_content

    path = "test/special.txt"
    await file_system_manager.write_file(path, combined_content)

    read_content = await file_system_manager.read_file(path)

    assert read_content == combined_content


@settings(max_examples=20)
@given(
    updates=st.lists(
        st.text(min_size=1, max_size=1000),
        min_size=1,
        max_size=10,
    ),
)
@pytest.mark.asyncio
async def test_multiple_updates_consistency(
    file_system_manager: FileSystemManager,
    updates: list,
):
    """Test that multiple updates preserve consistency."""
    path = "test/updates.txt"

    for content in updates:
        await file_system_manager.write_file(path, content)
        read_content = await file_system_manager.read_file(path)
        assert read_content == content, f"Content mismatch after update"
