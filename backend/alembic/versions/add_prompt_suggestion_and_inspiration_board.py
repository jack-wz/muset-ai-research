"""Add PromptSuggestion and InspirationBoard models

Revision ID: add_prompt_inspiration
Revises: add_writing_styles
Create Date: 2025-01-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_prompt_inspiration'
down_revision: Union[str, None] = 'add_writing_styles'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create PromptSuggestion and InspirationBoard tables."""

    # Create prompt_suggestions table
    op.create_table(
        'prompt_suggestions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'category',
            sa.String(),
            nullable=False,
            comment='Category: question, theme, angle, community-sample'
        ),
        sa.Column('text', sa.Text(), nullable=False, comment='Prompt suggestion text'),
        sa.Column('icon', sa.String(), nullable=True, comment='Icon identifier or emoji'),
        sa.Column(
            'tags',
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default='{}',
            comment='Tags for filtering suggestions'
        ),
        sa.Column(
            'locale',
            sa.String(),
            nullable=False,
            server_default='en',
            comment='Language code (en, zh, etc.)'
        ),
        sa.Column(
            'required_skills',
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default='{}',
            comment='Required skill package names'
        ),
        sa.Column(
            'usage_count',
            sa.String(),
            nullable=False,
            server_default='0',
            comment='Number of times this suggestion was used'
        ),
        sa.Column('rating', sa.String(), nullable=True, comment='Average user rating (0-5)'),
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
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for prompt_suggestions
    op.create_index(
        op.f('ix_prompt_suggestions_category'),
        'prompt_suggestions',
        ['category'],
        unique=False
    )
    op.create_index(
        op.f('ix_prompt_suggestions_locale'),
        'prompt_suggestions',
        ['locale'],
        unique=False
    )

    # Create inspiration_boards table
    op.create_table(
        'inspiration_boards',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'workspace_id',
            postgresql.UUID(as_uuid=True),
            nullable=False
        ),
        sa.Column('title', sa.String(), nullable=False, comment='Inspiration board title'),
        sa.Column('description', sa.Text(), nullable=True, comment='Board description'),
        sa.Column(
            'related_page_ids',
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default='{}',
            comment='IDs of related pages'
        ),
        sa.Column(
            'suggestions',
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default='{}',
            comment='IDs of included prompt suggestions'
        ),
        sa.Column(
            'community_sample_ids',
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default='{}',
            comment='IDs of community examples'
        ),
        sa.Column('notes', sa.Text(), nullable=True, comment="User's custom notes for this board"),
        sa.Column(
            'status',
            sa.String(),
            nullable=False,
            server_default='active',
            comment='Board status: active, archived'
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
            ['workspace_id'],
            ['workspaces.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index for inspiration_boards
    op.create_index(
        op.f('ix_inspiration_boards_workspace_id'),
        'inspiration_boards',
        ['workspace_id'],
        unique=False
    )


def downgrade() -> None:
    """Drop PromptSuggestion and InspirationBoard tables."""

    # Drop inspiration_boards table
    op.drop_index(
        op.f('ix_inspiration_boards_workspace_id'),
        table_name='inspiration_boards'
    )
    op.drop_table('inspiration_boards')

    # Drop prompt_suggestions table
    op.drop_index(
        op.f('ix_prompt_suggestions_locale'),
        table_name='prompt_suggestions'
    )
    op.drop_index(
        op.f('ix_prompt_suggestions_category'),
        table_name='prompt_suggestions'
    )
    op.drop_table('prompt_suggestions')
