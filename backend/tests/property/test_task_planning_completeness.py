"""Property test: Task planning completeness.

Verifies requirements 1.1, 1.2.
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from langchain_core.messages import AIMessage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, MagicMock

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
    # Return valid JSON response
    llm.ainvoke.return_value = AIMessage(
        content="""{
  "analysis": "Test analysis",
  "tasks": [
    {
      "title": "Task 1",
      "description": "First task",
      "type": "outline",
      "priority": "high",
      "dependencies": []
    },
    {
      "title": "Task 2",
      "description": "Second task",
      "type": "draft",
      "priority": "medium",
      "dependencies": ["0"]
    }
  ]
}"""
    )
    return llm


@pytest.fixture
async def task_planner(test_db, mock_llm):
    """Create a task planner for testing."""
    planner = TaskPlanner(session=test_db, llm=mock_llm)
    yield planner


# Property 1: Task planning completeness
@settings(max_examples=50)
@given(
    goal=st.text(min_size=10, max_size=500),
)
@pytest.mark.asyncio
async def test_plan_contains_at_least_one_task(
    task_planner: TaskPlanner,
    goal: str,
):
    """
    Test that planning generates at least one task.

    This property verifies:
    - Goal analysis produces a plan (Req 1.1)
    - Plan contains actionable tasks (Req 1.2)
    """
    plan = await task_planner.create_todos(
        workspace_id="test-workspace",
        goal=goal,
    )

    assert plan is not None
    assert len(plan.tasks) >= 1, "Plan should contain at least one task"


@pytest.mark.asyncio
async def test_tasks_have_clear_descriptions(
    task_planner: TaskPlanner,
):
    """Test that all tasks have clear descriptions."""
    plan = await task_planner.create_todos(
        workspace_id="test-workspace",
        goal="Write a blog post about AI",
    )

    for task in plan.tasks:
        assert len(task.title) > 0, "Task should have a title"
        assert len(task.description) > 0, "Task should have a description"
        assert task.step_type in ["outline", "draft", "research", "edit", "publish"]


@pytest.mark.asyncio
async def test_dependencies_form_dag(
    task_planner: TaskPlanner,
):
    """Test that task dependencies form a DAG (no cycles)."""
    plan = await task_planner.create_todos(
        workspace_id="test-workspace",
        goal="Write a technical article",
    )

    validation = await task_planner.validate_dependencies(plan.id)

    assert validation["valid"], "Task dependencies should form a DAG"
