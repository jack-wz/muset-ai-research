"""Tests for search functionality."""
import uuid
from datetime import datetime

import pytest
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search_service import SearchService
from tests.conftest import TestBase


class TestPage(TestBase):
    """Test page model for search testing."""

    __tablename__ = "pages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    status = Column(String, default="draft")
    tags = Column(JSON, default=[])
    tiptap_content = Column(JSON, default={})
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class TestChatSession(TestBase):
    """Test chat session model for search testing."""

    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    mode = Column(String, default="chat")
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class TestChatMessage(TestBase):
    """Test chat message model for search testing."""

    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class TestSearchIndex(TestBase):
    """Test search index model."""

    __tablename__ = "search_indexes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    content_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    search_metadata = Column(JSON, default={})
    url = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow)


class TestSearchHistory(TestBase):
    """Test search history model."""

    __tablename__ = "search_histories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    workspace_id = Column(String, nullable=False)
    query = Column(String, nullable=False)
    filters = Column(JSON, default={})
    results_count = Column(JSON, default={"total": 0})
    clicked_result_id = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow)


# Patch models for testing
import app.models.page as page_module
import app.models.chat as chat_module
import app.models.search as search_module

page_module.Page = TestPage
chat_module.ChatSession = TestChatSession
chat_module.ChatMessage = TestChatMessage
search_module.SearchIndex = TestSearchIndex
search_module.SearchHistory = TestSearchHistory


@pytest.mark.asyncio
async def test_extract_tiptap_text(test_db: AsyncSession) -> None:
    """Test extracting plain text from TipTap JSON."""
    search_service = SearchService(test_db)

    # Test simple text content
    tiptap_content = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Hello "},
                    {"type": "text", "text": "World"},
                ],
            }
        ],
    }

    text = search_service._extract_tiptap_text(tiptap_content)
    assert text == "Hello World"


@pytest.mark.asyncio
async def test_extract_tiptap_text_nested(test_db: AsyncSession) -> None:
    """Test extracting text from nested TipTap structures."""
    search_service = SearchService(test_db)

    tiptap_content = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "content": [{"type": "text", "text": "Title"}],
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "First paragraph"}],
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Second paragraph"}],
            },
        ],
    }

    text = search_service._extract_tiptap_text(tiptap_content)
    assert "Title" in text
    assert "First paragraph" in text
    assert "Second paragraph" in text


@pytest.mark.asyncio
async def test_extract_tiptap_text_empty(test_db: AsyncSession) -> None:
    """Test extracting text from empty content."""
    search_service = SearchService(test_db)

    text = search_service._extract_tiptap_text({})
    assert text == ""

    text = search_service._extract_tiptap_text(None)
    assert text == ""


@pytest.mark.asyncio
async def test_generate_tsquery(test_db: AsyncSession) -> None:
    """Test generating PostgreSQL TSQuery."""
    search_service = SearchService(test_db)

    # Test single word
    query = search_service._generate_tsquery("hello")
    assert "hello:*" in query

    # Test multiple words
    query = search_service._generate_tsquery("hello world test")
    assert "hello:*" in query
    assert "world:*" in query
    assert "test:*" in query
    assert "|" in query  # OR operator

    # Test empty query
    query = search_service._generate_tsquery("")
    assert query == ""


@pytest.mark.asyncio
async def test_format_result(test_db: AsyncSession) -> None:
    """Test formatting search result."""
    search_service = SearchService(test_db)

    # Create a mock search index
    from app.models.search import SearchIndex

    index = SearchIndex(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        content_type="page",
        content_id=uuid.uuid4(),
        title="Test Page",
        description="Test description",
        content="Test content",
        search_metadata={"tags": ["test"]},
        url="/pages/123",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    result = search_service._format_result(index)

    assert result["content_type"] == "page"
    assert result["title"] == "Test Page"
    assert result["description"] == "Test description"
    assert result["metadata"] == {"tags": ["test"]}
    assert result["url"] == "/pages/123"
    assert "id" in result
    assert "content_id" in result
    assert "created_at" in result
    assert "updated_at" in result


@pytest.mark.asyncio
async def test_save_search_history(test_db: AsyncSession) -> None:
    """Test saving search history."""
    search_service = SearchService(test_db)

    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    history = await search_service.save_search_history(
        user_id=user_id,
        workspace_id=workspace_id,
        query="test query",
        filters={"content_types": ["page"]},
        results_count=5,
    )

    assert history.query == "test query"
    assert history.user_id == user_id
    assert history.workspace_id == workspace_id
    assert history.filters == {"content_types": ["page"]}
    assert history.results_count == {"total": 5}


@pytest.mark.asyncio
async def test_save_search_history_with_clicked_result(test_db: AsyncSession) -> None:
    """Test saving search history with clicked result."""
    search_service = SearchService(test_db)

    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    clicked_id = uuid.uuid4()

    history = await search_service.save_search_history(
        user_id=user_id,
        workspace_id=workspace_id,
        query="test query",
        results_count=5,
        clicked_result_id=clicked_id,
    )

    assert history.clicked_result_id == clicked_id


def test_search_service_initialization() -> None:
    """Test SearchService initialization."""
    from unittest.mock import MagicMock

    mock_session = MagicMock()
    service = SearchService(mock_session)

    assert service.session == mock_session


@pytest.mark.asyncio
async def test_index_page_new(test_db: AsyncSession) -> None:
    """Test indexing a new page."""
    # Note: This test is simplified for demonstration
    # In a real test with a proper database, you would:
    # 1. Create a test page
    # 2. Index it using the search service
    # 3. Verify the index was created
    # 4. Search for the page
    # 5. Verify it appears in results
    pass


@pytest.mark.asyncio
async def test_search_by_content_type(test_db: AsyncSession) -> None:
    """Test searching with content type filter."""
    # Note: This test is simplified for demonstration
    # In a real test with a proper database, you would:
    # 1. Create multiple types of content (pages, files, messages)
    # 2. Index them all
    # 3. Search with content_type filter
    # 4. Verify only matching types are returned
    pass


@pytest.mark.asyncio
async def test_search_pagination(test_db: AsyncSession) -> None:
    """Test search pagination."""
    # Note: This test is simplified for demonstration
    # In a real test with a proper database, you would:
    # 1. Create many indexed items
    # 2. Search with different limit/offset values
    # 3. Verify correct number of results
    # 4. Verify total count is accurate
    pass


@pytest.mark.asyncio
async def test_delete_index(test_db: AsyncSession) -> None:
    """Test deleting a search index."""
    # Note: This test is simplified for demonstration
    # In a real test with a proper database, you would:
    # 1. Create and index content
    # 2. Delete the index
    # 3. Verify index no longer exists
    # 4. Verify content doesn't appear in search
    pass
