"""Unit tests for MemoryManager."""
import pytest
from langchain_core.embeddings import FakeEmbeddings
from langchain_core.messages import AIMessage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock

from app.db.base import Base
from app.services.memory_manager import MemoryManager


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
def mock_llm():
    """Create a mock LLM."""
    llm = AsyncMock()
    llm.ainvoke.return_value = AIMessage(
        content="""{
  "toneDescriptors": ["professional", "clear"],
  "pacing": "moderate",
  "sentenceLength": "medium",
  "complexity": "moderate",
  "dos": ["Use active voice", "Be concise"],
  "donts": ["Avoid jargon", "Don't be verbose"]
}"""
    )
    return llm


@pytest.fixture
async def memory_manager(test_db, mock_llm):
    """Create a memory manager for testing."""
    embeddings = FakeEmbeddings(size=1536)
    return MemoryManager(
        session=test_db,
        llm=mock_llm,
        embeddings=embeddings,
    )


@pytest.mark.asyncio
async def test_store_style_profile(memory_manager: MemoryManager):
    """Test storing a style profile."""
    samples = [
        "This is a professional writing sample.",
        "It demonstrates clear and concise communication.",
    ]

    memory = await memory_manager.store_style_profile(
        workspace_id="test-workspace",
        samples=samples,
        title="Professional Style",
    )

    assert memory is not None
    assert memory.type == "style"
    assert "samples" in memory.payload


@pytest.mark.asyncio
async def test_store_glossary_term(memory_manager: MemoryManager):
    """Test storing a glossary term."""
    memory = await memory_manager.store_glossary_term(
        workspace_id="test-workspace",
        term="API",
        definition="Application Programming Interface",
        usage_examples=["The API allows developers to integrate our service."],
    )

    assert memory is not None
    assert memory.type == "glossary"
    assert memory.payload["term"] == "API"


@pytest.mark.asyncio
async def test_load_memories(memory_manager: MemoryManager):
    """Test loading memories."""
    # Store some memories
    await memory_manager.store_glossary_term(
        workspace_id="test-workspace",
        term="REST",
        definition="Representational State Transfer",
    )

    # Load memories
    memories = await memory_manager.load_memories(
        workspace_id="test-workspace",
        query="API architecture",
        memory_type="glossary",
    )

    assert len(memories) > 0


@pytest.mark.asyncio
async def test_store_knowledge(memory_manager: MemoryManager):
    """Test storing knowledge."""
    memory = await memory_manager.store_knowledge(
        workspace_id="test-workspace",
        topic="Machine Learning Basics",
        summary="ML is a subset of AI that enables systems to learn from data.",
        citations=["https://example.com/ml-intro"],
    )

    assert memory is not None
    assert memory.type == "knowledge"


@pytest.mark.asyncio
async def test_store_preference(memory_manager: MemoryManager):
    """Test storing a preference."""
    memory = await memory_manager.store_preference(
        workspace_id="test-workspace",
        key="tone",
        value="professional",
        context="For business communications",
    )

    assert memory is not None
    assert memory.type == "preference"
    assert memory.payload["key"] == "tone"
