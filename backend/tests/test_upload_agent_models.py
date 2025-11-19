"""
Tests for UploadAsset, AgentRun, AgentStep, and SubAgentContext Models

This module tests file upload tracking and agent runtime models.
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Create a test base compatible with SQLite
TestBase = declarative_base()


# Simplified models for testing (SQLite compatible)
class TestUploadAsset(TestBase):
    """Test upload asset model (SQLite compatible)."""

    __tablename__ = "upload_assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, nullable=False)
    uploader_id = Column(String, nullable=True)
    file_id = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    status = Column(String, default="processing", nullable=False)
    processing_metadata = Column(JSON, default={})
    error_message = Column(Text, nullable=True)
    mime_type = Column(String, nullable=True)
    file_size = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestAgentRun(TestBase):
    """Test agent run model (SQLite compatible)."""

    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False)
    plan_id = Column(String, nullable=True)
    trigger = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)
    current_step_id = Column(String, nullable=True)
    related_sub_agents = Column(JSON, default=[])
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, default={})
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestAgentStep(TestBase):
    """Test agent step model (SQLite compatible)."""

    __tablename__ = "agent_steps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("agent_runs.id"), nullable=False)
    step_type = Column(String, nullable=False)
    name = Column(String, nullable=True)
    input_data = Column(JSON, default={}, nullable=False)
    output_data = Column(JSON, nullable=True)
    status = Column(String, default="pending", nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestSubAgentContext(TestBase):
    """Test sub-agent context model (SQLite compatible)."""

    __tablename__ = "sub_agent_contexts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_run_id = Column(String, ForeignKey("agent_runs.id"), nullable=False)
    agent_type = Column(String, nullable=False)
    scoped_files = Column(JSON, default=[])
    scoped_memories = Column(JSON, default=[])
    temp_directory = Column(String, nullable=True)
    instructions = Column(Text, nullable=False)
    result_file_id = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)
    error_message = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Fixtures
@pytest.fixture(scope="module")
def test_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:")
    TestBase.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine) -> Session:
    """Create a new database session for a test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


class TestUploadAssetModel:
    """Test suite for UploadAsset model."""

    def test_create_upload_asset(self, test_session: Session):
        """Test creating an upload asset."""
        workspace_id = str(uuid.uuid4())
        uploader_id = str(uuid.uuid4())
        file_id = str(uuid.uuid4())

        asset = TestUploadAsset(
            workspace_id=workspace_id,
            uploader_id=uploader_id,
            file_id=file_id,
            original_name="document.pdf",
            file_type="document",
            mime_type="application/pdf",
            file_size="1024000",
        )

        test_session.add(asset)
        test_session.commit()

        assert asset.id is not None
        assert asset.workspace_id == workspace_id
        assert asset.original_name == "document.pdf"
        assert asset.file_type == "document"
        assert asset.status == "processing"
        assert asset.created_at is not None

    def test_upload_asset_status_tracking(self, test_session: Session):
        """Test tracking upload asset processing status."""
        asset = TestUploadAsset(
            workspace_id=str(uuid.uuid4()),
            file_id=str(uuid.uuid4()),
            original_name="image.png",
            file_type="image",
            status="processing",
        )

        test_session.add(asset)
        test_session.commit()

        # Simulate successful processing
        asset.status = "ready"
        asset.processing_metadata = {
            "thumbnailFileId": str(uuid.uuid4()),
            "extractedTextFileId": str(uuid.uuid4()),
        }
        test_session.commit()

        # Verify status update
        retrieved = test_session.query(TestUploadAsset).filter_by(id=asset.id).first()
        assert retrieved.status == "ready"
        assert "thumbnailFileId" in retrieved.processing_metadata

    def test_upload_asset_failed_processing(self, test_session: Session):
        """Test upload asset with failed processing."""
        asset = TestUploadAsset(
            workspace_id=str(uuid.uuid4()),
            file_id=str(uuid.uuid4()),
            original_name="corrupt.docx",
            file_type="document",
            status="failed",
            error_message="Failed to extract text: corrupt file",
        )

        test_session.add(asset)
        test_session.commit()

        assert asset.status == "failed"
        assert asset.error_message is not None

    def test_upload_asset_ocr_status(self, test_session: Session):
        """Test upload asset with OCR processing."""
        asset = TestUploadAsset(
            workspace_id=str(uuid.uuid4()),
            file_id=str(uuid.uuid4()),
            original_name="scanned.pdf",
            file_type="document",
            processing_metadata={
                "ocrStatus": "completed",
                "extractedTextFileId": str(uuid.uuid4()),
            },
        )

        test_session.add(asset)
        test_session.commit()

        assert asset.processing_metadata.get("ocrStatus") == "completed"


class TestAgentRunModel:
    """Test suite for AgentRun model."""

    def test_create_agent_run(self, test_session: Session):
        """Test creating an agent run."""
        session_id = str(uuid.uuid4())
        plan_id = str(uuid.uuid4())

        run = TestAgentRun(
            session_id=session_id,
            plan_id=plan_id,
            trigger="user_request",
            status="pending",
        )

        test_session.add(run)
        test_session.commit()

        assert run.id is not None
        assert run.session_id == session_id
        assert run.plan_id == plan_id
        assert run.trigger == "user_request"
        assert run.status == "pending"

    def test_agent_run_status_transitions(self, test_session: Session):
        """Test agent run status transitions."""
        run = TestAgentRun(
            session_id=str(uuid.uuid4()),
            trigger="user_request",
            status="pending",
        )

        test_session.add(run)
        test_session.commit()

        # Transition to running
        run.status = "running"
        run.started_at = datetime.utcnow()
        test_session.commit()

        # Transition to completed
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        test_session.commit()

        retrieved = test_session.query(TestAgentRun).filter_by(id=run.id).first()
        assert retrieved.status == "completed"
        assert retrieved.started_at is not None
        assert retrieved.completed_at is not None

    def test_agent_run_with_error(self, test_session: Session):
        """Test agent run with error."""
        run = TestAgentRun(
            session_id=str(uuid.uuid4()),
            trigger="system",
            status="failed",
            error_message="Execution timeout after 300 seconds",
        )

        test_session.add(run)
        test_session.commit()

        assert run.status == "failed"
        assert run.error_message is not None

    def test_agent_run_with_sub_agents(self, test_session: Session):
        """Test agent run with related sub-agents."""
        sub_agent_id1 = str(uuid.uuid4())
        sub_agent_id2 = str(uuid.uuid4())

        run = TestAgentRun(
            session_id=str(uuid.uuid4()),
            trigger="user_request",
            related_sub_agents=[sub_agent_id1, sub_agent_id2],
        )

        test_session.add(run)
        test_session.commit()

        assert len(run.related_sub_agents) == 2
        assert sub_agent_id1 in run.related_sub_agents


class TestAgentStepModel:
    """Test suite for AgentStep model."""

    def test_create_agent_step(self, test_session: Session):
        """Test creating an agent step."""
        # Create parent run first
        run = TestAgentRun(
            session_id=str(uuid.uuid4()),
            trigger="user_request",
        )
        test_session.add(run)
        test_session.commit()

        # Create step
        step = TestAgentStep(
            run_id=run.id,
            step_type="plan",
            name="Generate writing outline",
            input_data={"prompt": "Create an outline for a blog post"},
        )

        test_session.add(step)
        test_session.commit()

        assert step.id is not None
        assert step.run_id == run.id
        assert step.step_type == "plan"
        assert step.name == "Generate writing outline"

    def test_agent_step_execution(self, test_session: Session):
        """Test agent step execution tracking."""
        run = TestAgentRun(
            session_id=str(uuid.uuid4()),
            trigger="user_request",
        )
        test_session.add(run)
        test_session.commit()

        step = TestAgentStep(
            run_id=run.id,
            step_type="tool",
            name="Search for references",
            input_data={"query": "AI writing tools"},
            status="pending",
        )
        test_session.add(step)
        test_session.commit()

        # Start execution
        step.status = "running"
        step.started_at = datetime.utcnow()
        test_session.commit()

        # Complete execution
        step.status = "completed"
        step.finished_at = datetime.utcnow()
        step.output_data = {"results": ["result1", "result2"]}
        test_session.commit()

        retrieved = test_session.query(TestAgentStep).filter_by(id=step.id).first()
        assert retrieved.status == "completed"
        assert retrieved.output_data is not None

    def test_agent_step_types(self, test_session: Session):
        """Test creating steps with different types."""
        run = TestAgentRun(
            session_id=str(uuid.uuid4()),
            trigger="user_request",
        )
        test_session.add(run)
        test_session.commit()

        step_types = ["plan", "tool", "file_op", "skill_activation", "mcp_call"]

        for step_type in step_types:
            step = TestAgentStep(
                run_id=run.id,
                step_type=step_type,
                input_data={"test": "data"},
            )
            test_session.add(step)

        test_session.commit()

        # Verify all steps were created
        steps = test_session.query(TestAgentStep).filter_by(run_id=run.id).all()
        assert len(steps) == len(step_types)


class TestSubAgentContextModel:
    """Test suite for SubAgentContext model."""

    def test_create_sub_agent_context(self, test_session: Session):
        """Test creating a sub-agent context."""
        # Create parent run
        run = TestAgentRun(
            session_id=str(uuid.uuid4()),
            trigger="user_request",
        )
        test_session.add(run)
        test_session.commit()

        # Create sub-agent context
        context = TestSubAgentContext(
            parent_run_id=run.id,
            agent_type="research",
            instructions="Research AI writing trends for 2024",
            temp_directory="/tmp/subagent-research-123",
        )

        test_session.add(context)
        test_session.commit()

        assert context.id is not None
        assert context.parent_run_id == run.id
        assert context.agent_type == "research"
        assert context.status == "pending"

    def test_sub_agent_with_scoped_resources(self, test_session: Session):
        """Test sub-agent with scoped files and memories."""
        run = TestAgentRun(
            session_id=str(uuid.uuid4()),
            trigger="user_request",
        )
        test_session.add(run)
        test_session.commit()

        file_id1 = str(uuid.uuid4())
        file_id2 = str(uuid.uuid4())
        memory_id1 = str(uuid.uuid4())

        context = TestSubAgentContext(
            parent_run_id=run.id,
            agent_type="translation",
            scoped_files=[file_id1, file_id2],
            scoped_memories=[memory_id1],
            instructions="Translate content to Spanish",
        )

        test_session.add(context)
        test_session.commit()

        assert len(context.scoped_files) == 2
        assert len(context.scoped_memories) == 1

    def test_sub_agent_execution_lifecycle(self, test_session: Session):
        """Test sub-agent execution lifecycle."""
        run = TestAgentRun(
            session_id=str(uuid.uuid4()),
            trigger="system",
        )
        test_session.add(run)
        test_session.commit()

        context = TestSubAgentContext(
            parent_run_id=run.id,
            agent_type="editing",
            instructions="Edit for clarity and grammar",
            status="pending",
        )
        test_session.add(context)
        test_session.commit()

        # Start execution
        context.status = "running"
        test_session.commit()

        # Complete with result
        context.status = "completed"
        context.completed_at = datetime.utcnow()
        context.result_file_id = str(uuid.uuid4())
        test_session.commit()

        retrieved = test_session.query(TestSubAgentContext).filter_by(id=context.id).first()
        assert retrieved.status == "completed"
        assert retrieved.result_file_id is not None

    def test_sub_agent_types(self, test_session: Session):
        """Test different sub-agent types."""
        run = TestAgentRun(
            session_id=str(uuid.uuid4()),
            trigger="user_request",
        )
        test_session.add(run)
        test_session.commit()

        agent_types = ["research", "translation", "editing", "fact_check"]

        for agent_type in agent_types:
            context = TestSubAgentContext(
                parent_run_id=run.id,
                agent_type=agent_type,
                instructions=f"Perform {agent_type} task",
            )
            test_session.add(context)

        test_session.commit()

        # Verify all contexts were created
        contexts = test_session.query(TestSubAgentContext).filter_by(parent_run_id=run.id).all()
        assert len(contexts) == len(agent_types)


class TestIntegration:
    """Test integration between different models."""

    def test_complete_agent_run_workflow(self, test_session: Session):
        """Test a complete agent run with steps and sub-agents."""
        # Create agent run
        run = TestAgentRun(
            session_id=str(uuid.uuid4()),
            trigger="user_request",
            status="running",
            started_at=datetime.utcnow(),
        )
        test_session.add(run)
        test_session.commit()

        # Create steps
        step1 = TestAgentStep(
            run_id=run.id,
            step_type="plan",
            name="Create plan",
            input_data={"goal": "Write article"},
            status="completed",
            output_data={"plan_id": str(uuid.uuid4())},
        )
        step2 = TestAgentStep(
            run_id=run.id,
            step_type="tool",
            name="Research",
            input_data={"query": "AI trends"},
            status="running",
        )

        test_session.add_all([step1, step2])
        test_session.commit()

        # Create sub-agent
        sub_agent = TestSubAgentContext(
            parent_run_id=run.id,
            agent_type="research",
            instructions="Research AI trends",
            status="running",
        )
        test_session.add(sub_agent)
        test_session.commit()

        # Verify relationships
        steps = test_session.query(TestAgentStep).filter_by(run_id=run.id).all()
        sub_agents = test_session.query(TestSubAgentContext).filter_by(parent_run_id=run.id).all()

        assert len(steps) == 2
        assert len(sub_agents) == 1
        assert run.status == "running"
