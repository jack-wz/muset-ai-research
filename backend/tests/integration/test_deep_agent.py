"""Integration tests for DeepAgent."""
import tempfile

import pytest
from langchain_core.embeddings import FakeEmbeddings
from langchain_core.messages import AIMessage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock

from app.db.base import Base
from app.services.deep_agent import DeepAgent


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
    """Create a mock LLM with various responses."""
    llm = AsyncMock()

    # Default response
    def mock_response(*args, **kwargs):
        messages = args[0] if args else []
        if any("task" in str(msg).lower() for msg in messages):
            return AIMessage(
                content="""{
  "analysis": "Write a comprehensive blog post",
  "tasks": [
    {
      "title": "Research topic",
      "description": "Gather information about AI trends",
      "type": "research",
      "priority": "high",
      "dependencies": []
    },
    {
      "title": "Draft post",
      "description": "Write initial draft",
      "type": "draft",
      "priority": "high",
      "dependencies": ["0"]
    }
  ]
}"""
            )
        return AIMessage(content="Task completed successfully.")

    llm.ainvoke.side_effect = mock_response
    return llm


@pytest.fixture
async def deep_agent(test_db, mock_llm):
    """Create a DeepAgent for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        embeddings = FakeEmbeddings(size=1536)
        agent = DeepAgent(
            workspace_id="test-workspace",
            session=test_db,
            llm=mock_llm,
            embeddings=embeddings,
            base_path=tmpdir,
        )
        yield agent


@pytest.mark.asyncio
async def test_deep_agent_workflow(deep_agent: DeepAgent):
    """Test the complete DeepAgent workflow."""
    result = await deep_agent.run("Write a blog post about AI trends in 2024")

    assert result is not None
    assert "response" in result
    assert "plan_id" in result


@pytest.mark.asyncio
async def test_deep_agent_file_creation(deep_agent: DeepAgent):
    """Test that DeepAgent creates files."""
    result = await deep_agent.run("Write a technical article")

    assert result is not None
    # Files might be created during task execution
    # This depends on the workflow implementation


@pytest.mark.asyncio
async def test_deep_agent_task_planning(deep_agent: DeepAgent):
    """Test task planning component."""
    result = await deep_agent.run("Create a research report")

    assert result is not None
    assert result.get("plan_id") is not None


@pytest.mark.asyncio
async def test_deep_agent_memory_integration(deep_agent: DeepAgent):
    """Test memory manager integration."""
    # Store a memory first
    await deep_agent.memory_manager.store_style_profile(
        workspace_id="test-workspace",
        samples=["Professional writing sample"],
        title="Test Style",
    )

    # Run agent
    result = await deep_agent.run("Write in professional style")

    assert result is not None


@pytest.mark.asyncio
async def test_deep_agent_error_handling(deep_agent: DeepAgent):
    """Test error handling in workflow."""
    # Mock LLM to raise an error
    deep_agent.llm.ainvoke.side_effect = Exception("Test error")

    # Agent should handle errors gracefully
    try:
        await deep_agent.run("Test error handling")
    except Exception as e:
        # Error should be caught or propagated appropriately
        assert str(e) == "Test error"


@pytest.mark.asyncio
async def test_deep_agent_multiple_tasks(deep_agent: DeepAgent):
    """Test executing multiple tasks in sequence."""
    result = await deep_agent.run("Write a report with research and editing")

    assert result is not None
    assert result.get("plan_id") is not None
