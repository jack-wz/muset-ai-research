"""Writing plan and task models."""
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin, WorkspaceMixin


class WritingPlan(Base, BaseMixin, WorkspaceMixin):
    """Writing plan model."""

    __tablename__ = "writing_plans"

    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    page_id = Column(UUID(as_uuid=True), nullable=True)
    goal = Column(Text, nullable=False)
    source_prompt = Column(Text, nullable=False)
    status = Column(
        String,
        default="pending",
        nullable=False,
    )  # pending, active, completed, archived
    current_task_id = Column(UUID(as_uuid=True), nullable=True)

    # Task IDs as array
    task_ids = Column(ARRAY(String), default=[], nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="writing_plans")
    tasks = relationship("TodoTask", back_populates="plan", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation."""
        return f"<WritingPlan {self.id}>"


class TodoTask(Base, BaseMixin):
    """Todo task model."""

    __tablename__ = "todo_tasks"

    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("writing_plans.id"),
        nullable=False,
        index=True,
    )
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(
        String,
        default="pending",
        nullable=False,
    )  # pending, in_progress, blocked, completed
    step_type = Column(
        String,
        nullable=False,
    )  # outline, draft, research, edit, publish
    priority = Column(String, default="medium", nullable=False)  # low, medium, high

    # Dependencies and outputs
    dependencies = Column(ARRAY(String), default=[], nullable=False)
    outputs = Column(JSONB, default=[], nullable=False)

    # Agent assignment
    assigned_agent_id = Column(String, nullable=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    plan = relationship("WritingPlan", back_populates="tasks")

    def __repr__(self) -> str:
        """String representation."""
        return f"<TodoTask {self.title}>"
