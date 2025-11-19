"""Add SearchIndex and SearchHistory models for global search

Revision ID: add_search_models
Revises: add_audit_subscription
Create Date: 2025-01-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_search_models'
down_revision: Union[str, None] = 'add_audit_subscription'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create search_indexes table
    op.create_table(
        'search_indexes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.Column('search_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('url', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for search_indexes
    op.create_index('ix_search_indexes_workspace_id', 'search_indexes', ['workspace_id'])
    op.create_index('ix_search_indexes_content_type', 'search_indexes', ['content_type'])
    op.create_index('ix_search_indexes_content_id', 'search_indexes', ['content_id'])
    op.create_index('ix_search_indexes_workspace_content', 'search_indexes', ['workspace_id', 'content_type'])
    op.create_index('ix_search_indexes_content_unique', 'search_indexes', ['content_type', 'content_id'], unique=True)
    op.create_index('ix_search_indexes_search_vector', 'search_indexes', ['search_vector'], postgresql_using='gin')
    op.create_index('ix_search_indexes_metadata', 'search_indexes', ['search_metadata'], postgresql_using='gin')

    # Create search_histories table
    op.create_table(
        'search_histories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query', sa.String(), nullable=False),
        sa.Column('filters', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('results_count', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{"total": 0}'),
        sa.Column('clicked_result_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for search_histories
    op.create_index('ix_search_histories_user_id', 'search_histories', ['user_id'])
    op.create_index('ix_search_histories_workspace_id', 'search_histories', ['workspace_id'])
    op.create_index('ix_search_histories_user_workspace', 'search_histories', ['user_id', 'workspace_id', 'created_at'])


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop search_histories table and indexes
    op.drop_index('ix_search_histories_user_workspace', table_name='search_histories')
    op.drop_index('ix_search_histories_workspace_id', table_name='search_histories')
    op.drop_index('ix_search_histories_user_id', table_name='search_histories')
    op.drop_table('search_histories')

    # Drop search_indexes table and indexes
    op.drop_index('ix_search_indexes_metadata', table_name='search_indexes')
    op.drop_index('ix_search_indexes_search_vector', table_name='search_indexes')
    op.drop_index('ix_search_indexes_content_unique', table_name='search_indexes')
    op.drop_index('ix_search_indexes_workspace_content', table_name='search_indexes')
    op.drop_index('ix_search_indexes_content_id', table_name='search_indexes')
    op.drop_index('ix_search_indexes_content_type', table_name='search_indexes')
    op.drop_index('ix_search_indexes_workspace_id', table_name='search_indexes')
    op.drop_table('search_indexes')
