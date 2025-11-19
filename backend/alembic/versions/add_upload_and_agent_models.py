"""Add UploadAsset, AgentRun, AgentStep, and SubAgentContext models

Revision ID: add_upload_agent
Revises: add_prompt_inspiration
Create Date: 2025-01-19 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_upload_agent'
down_revision: Union[str, None] = 'add_prompt_inspiration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create UploadAsset, AgentRun, AgentStep, and SubAgentContext tables."""

    # Create upload_assets table
    op.create_table(
        'upload_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'workspace_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            'uploader_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            'file_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column('original_name', sa.String(), nullable=False),
        sa.Column(
            'file_type',
            sa.String(),
            nullable=False,
            comment='File type: document, image, audio, video, spreadsheet, presentation'
        ),
        sa.Column(
            'status',
            sa.String(),
            nullable=False,
            server_default='processing',
            comment='Processing status: processing, ready, failed'
        ),
        sa.Column(
            'processing_metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Processing metadata including extracted text, thumbnails, OCR status'
        ),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('file_size', sa.String(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['workspace_id'],
            ['workspaces.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['uploader_id'],
            ['users.id'],
            ondelete='SET NULL'
        ),
        sa.ForeignKeyConstraint(
            ['file_id'],
            ['context_files.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for upload_assets
    op.create_index(
        op.f('ix_upload_assets_workspace_id'),
        'upload_assets',
        ['workspace_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_upload_assets_uploader_id'),
        'upload_assets',
        ['uploader_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_upload_assets_file_id'),
        'upload_assets',
        ['file_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_upload_assets_file_type'),
        'upload_assets',
        ['file_type'],
        unique=False
    )
    op.create_index(
        op.f('ix_upload_assets_status'),
        'upload_assets',
        ['status'],
        unique=False
    )

    # Create agent_runs table
    op.create_table(
        'agent_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'session_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            'plan_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            'trigger',
            sa.String(),
            nullable=False,
            comment='Trigger type: user_request, scheduled, system'
        ),
        sa.Column(
            'status',
            sa.String(),
            nullable=False,
            server_default='pending',
            comment='Status: pending, running, paused, completed, failed'
        ),
        sa.Column(
            'current_step_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            'related_sub_agents',
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default='{}',
        ),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['session_id'],
            ['chat_sessions.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['plan_id'],
            ['writing_plans.id'],
            ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for agent_runs
    op.create_index(
        op.f('ix_agent_runs_session_id'),
        'agent_runs',
        ['session_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_agent_runs_plan_id'),
        'agent_runs',
        ['plan_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_agent_runs_trigger'),
        'agent_runs',
        ['trigger'],
        unique=False
    )
    op.create_index(
        op.f('ix_agent_runs_status'),
        'agent_runs',
        ['status'],
        unique=False
    )

    # Create agent_steps table
    op.create_table(
        'agent_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'run_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            'step_type',
            sa.String(),
            nullable=False,
            comment='Step type: plan, tool, file_op, skill_activation, mcp_call'
        ),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column(
            'input_data',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='{}',
        ),
        sa.Column(
            'output_data',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            'status',
            sa.String(),
            nullable=False,
            server_default='pending',
        ),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['run_id'],
            ['agent_runs.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for agent_steps
    op.create_index(
        op.f('ix_agent_steps_run_id'),
        'agent_steps',
        ['run_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_agent_steps_step_type'),
        'agent_steps',
        ['step_type'],
        unique=False
    )

    # Create sub_agent_contexts table
    op.create_table(
        'sub_agent_contexts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'parent_run_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            'agent_type',
            sa.String(),
            nullable=False,
            comment='Agent type: research, translation, editing, fact_check'
        ),
        sa.Column(
            'scoped_files',
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default='{}',
        ),
        sa.Column(
            'scoped_memories',
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default='{}',
        ),
        sa.Column('temp_directory', sa.String(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=False),
        sa.Column('result_file_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            'status',
            sa.String(),
            nullable=False,
            server_default='pending',
        ),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ['parent_run_id'],
            ['agent_runs.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for sub_agent_contexts
    op.create_index(
        op.f('ix_sub_agent_contexts_parent_run_id'),
        'sub_agent_contexts',
        ['parent_run_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_sub_agent_contexts_agent_type'),
        'sub_agent_contexts',
        ['agent_type'],
        unique=False
    )


def downgrade() -> None:
    """Drop UploadAsset, AgentRun, AgentStep, and SubAgentContext tables."""

    # Drop sub_agent_contexts table
    op.drop_index(
        op.f('ix_sub_agent_contexts_agent_type'),
        table_name='sub_agent_contexts'
    )
    op.drop_index(
        op.f('ix_sub_agent_contexts_parent_run_id'),
        table_name='sub_agent_contexts'
    )
    op.drop_table('sub_agent_contexts')

    # Drop agent_steps table
    op.drop_index(
        op.f('ix_agent_steps_step_type'),
        table_name='agent_steps'
    )
    op.drop_index(
        op.f('ix_agent_steps_run_id'),
        table_name='agent_steps'
    )
    op.drop_table('agent_steps')

    # Drop agent_runs table
    op.drop_index(
        op.f('ix_agent_runs_status'),
        table_name='agent_runs'
    )
    op.drop_index(
        op.f('ix_agent_runs_trigger'),
        table_name='agent_runs'
    )
    op.drop_index(
        op.f('ix_agent_runs_plan_id'),
        table_name='agent_runs'
    )
    op.drop_index(
        op.f('ix_agent_runs_session_id'),
        table_name='agent_runs'
    )
    op.drop_table('agent_runs')

    # Drop upload_assets table
    op.drop_index(
        op.f('ix_upload_assets_status'),
        table_name='upload_assets'
    )
    op.drop_index(
        op.f('ix_upload_assets_file_type'),
        table_name='upload_assets'
    )
    op.drop_index(
        op.f('ix_upload_assets_file_id'),
        table_name='upload_assets'
    )
    op.drop_index(
        op.f('ix_upload_assets_uploader_id'),
        table_name='upload_assets'
    )
    op.drop_index(
        op.f('ix_upload_assets_workspace_id'),
        table_name='upload_assets'
    )
    op.drop_table('upload_assets')
