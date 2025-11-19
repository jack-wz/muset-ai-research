"""Agent runtime models for DeepAgent execution tracking."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin


class AgentRun(Base, BaseMixin):
    """Agent run model for tracking agent execution."""

    __tablename__ = "agent_runs"

    # Session relationship
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Chat session ID",
    )

    # Plan relationship (optional)
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("writing_plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Writing plan ID if associated",
    )

    # Trigger type
    trigger = Column(
        String,
        nullable=False,
        index=True,
        comment="Trigger type: user_request, scheduled, system",
    )

    # Execution status
    status = Column(
        String,
        default="pending",
        nullable=False,
        index=True,
        comment="Status: pending, running, paused, completed, failed",
    )

    # Current step being executed
    current_step_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Current step ID being executed",
    )

    # Related sub-agents
    related_sub_agents = Column(
        ARRAY(UUID(as_uuid=True)),
        default=[],
        nullable=False,
        comment="IDs of related sub-agent contexts",
    )

    # Error information
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if execution failed",
    )

    # Execution metadata
    meta = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Additional execution metadata",
    )

    # Execution times
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Execution start time",
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Execution completion time",
    )

    # Relationships
    session = relationship("ChatSession", back_populates="agent_runs")
    plan = relationship("WritingPlan", back_populates="agent_runs")
    steps = relationship(
        "AgentStep",
        back_populates="agent_run",
        cascade="all, delete-orphan",
        order_by="AgentStep.created_at",
    )
    sub_agent_contexts = relationship("SubAgentContext", back_populates="parent_run")

    def __repr__(self) -> str:
        """String representation."""
        return f"<AgentRun {self.id} ({self.status})>"

    def is_running(self) -> bool:
        """Check if agent run is currently running."""
        return self.status == "running"

    def is_completed(self) -> bool:
        """Check if agent run is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if agent run failed."""
        return self.status == "failed"

    def get_duration(self) -> float | None:
        """Get execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class AgentStep(Base, BaseMixin):
    """Agent step model for tracking individual execution steps."""

    __tablename__ = "agent_steps"

    # Agent run relationship
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Agent run ID",
    )

    # Step type
    step_type = Column(
        String,
        nullable=False,
        index=True,
        comment="Step type: plan, tool, file_op, skill_activation, mcp_call",
    )

    # Step name/description
    name = Column(
        String,
        nullable=True,
        comment="Step name or description",
    )

    # Input data
    input_data = Column(
        JSONB,
        nullable=False,
        default={},
        comment="Input data for this step",
    )

    # Output data
    output_data = Column(
        JSONB,
        nullable=True,
        comment="Output data from this step",
    )

    # Execution status
    status = Column(
        String,
        default="pending",
        nullable=False,
        comment="Status: pending, running, completed, failed",
    )

    # Error information
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if step failed",
    )

    # Execution times
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Step start time",
    )

    finished_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Step completion time",
    )

    # Additional metadata
    meta = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Additional step metadata",
    )

    # Relationships
    agent_run = relationship("AgentRun", back_populates="steps")

    def __repr__(self) -> str:
        """String representation."""
        return f"<AgentStep {self.step_type} ({self.status})>"

    def is_completed(self) -> bool:
        """Check if step is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if step failed."""
        return self.status == "failed"

    def get_duration(self) -> float | None:
        """Get step duration in seconds."""
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None


class SubAgentContext(Base, BaseMixin):
    """Sub-agent context model for isolated execution environments."""

    __tablename__ = "sub_agent_contexts"

    # Parent run relationship
    parent_run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent agent run ID",
    )

    # Agent type
    agent_type = Column(
        String,
        nullable=False,
        index=True,
        comment="Agent type: research, translation, editing, fact_check",
    )

    # Scoped files for this sub-agent
    scoped_files = Column(
        ARRAY(UUID(as_uuid=True)),
        default=[],
        nullable=False,
        comment="File IDs accessible to this sub-agent",
    )

    # Scoped memories for this sub-agent
    scoped_memories = Column(
        ARRAY(UUID(as_uuid=True)),
        default=[],
        nullable=False,
        comment="Memory IDs accessible to this sub-agent",
    )

    # Temporary directory path
    temp_directory = Column(
        String,
        nullable=True,
        comment="Temporary directory path for this sub-agent",
    )

    # Instructions for the sub-agent
    instructions = Column(
        Text,
        nullable=False,
        comment="Instructions for the sub-agent",
    )

    # Result file ID (output)
    result_file_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Result file ID produced by this sub-agent",
    )

    # Execution status
    status = Column(
        String,
        default="pending",
        nullable=False,
        comment="Status: pending, running, completed, failed",
    )

    # Error information
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if sub-agent execution failed",
    )

    # Completion time
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Completion time",
    )

    # Additional metadata
    meta = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Additional sub-agent metadata",
    )

    # Relationships
    parent_run = relationship("AgentRun", back_populates="sub_agent_contexts")

    def __repr__(self) -> str:
        """String representation."""
        return f"<SubAgentContext {self.agent_type} ({self.status})>"

    def is_completed(self) -> bool:
        """Check if sub-agent is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if sub-agent failed."""
        return self.status == "failed"

    def get_duration(self) -> float | None:
        """Get execution duration in seconds."""
        if self.created_at and self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None
