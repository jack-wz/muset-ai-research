"""Unit tests for TaskPlanner."""
import pytest
from langchain_core.messages import AIMessage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock

from app.db.base import Base
from app.services.task_planner import TaskPlanner


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
  "analysis": "Break down into research, writing, and editing phases",
  "tasks": [
    {
      "title": "Research topic",
      "description": "Gather information",
      "type": "research",
      "priority": "high",
      "dependencies": []
    },
    {
      "title": "Write draft",
      "description": "Create initial draft",
      "type": "draft",
      "priority": "high",
      "dependencies": ["0"]
    },
    {
      "title": "Edit and refine",
      "description": "Polish the content",
      "type": "edit",
      "priority": "medium",
      "dependencies": ["1"]
    }
  ]
}"""
    )
    return llm


@pytest.fixture
async def task_planner(test_db, mock_llm):
    """Create a task planner for testing."""
    return TaskPlanner(session=test_db, llm=mock_llm)


@pytest.mark.asyncio
async def test_create_todos(task_planner: TaskPlanner):
    """Test creating todos from a goal."""
    plan = await task_planner.create_todos(
        workspace_id="test-workspace",
        goal="Write a blog post about AI",
    )

    assert plan is not None
    assert len(plan.tasks) == 3
    assert plan.status == "active"


@pytest.mark.asyncio
async def test_analyze_goal(task_planner: TaskPlanner):
    """Test goal analysis."""
    analysis = await task_planner.analyze_goal("Write an article about climate change")

    assert "analysis" in analysis
    assert "tasks" in analysis
    assert len(analysis["tasks"]) > 0


@pytest.mark.asyncio
async def test_get_next_task(task_planner: TaskPlanner):
    """Test getting the next task."""
    plan = await task_planner.create_todos(
        workspace_id="test-workspace",
        goal="Write a report",
    )

    next_task = await task_planner.get_next_task(plan.id)
    assert next_task is not None
    assert next_task.status == "pending"


@pytest.mark.asyncio
async def test_validate_dependencies(task_planner: TaskPlanner):
    """Test dependency validation."""
    plan = await task_planner.create_todos(
        workspace_id="test-workspace",
        goal="Write a technical document",
    )

    validation = await task_planner.validate_dependencies(plan.id)
    assert validation["valid"] is True


@pytest.mark.asyncio
async def test_update_plan(task_planner: TaskPlanner):
    """Test updating a plan."""
    plan = await task_planner.create_todos(
        workspace_id="test-workspace",
        goal="Initial goal",
    )

    updated_plan = await task_planner.update_plan(
        plan.id,
        {"status": "completed"},
    )

    assert updated_plan.status == "completed"
