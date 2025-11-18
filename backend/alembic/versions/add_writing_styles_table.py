"""add_writing_styles_table

Revision ID: add_writing_styles
Revises: 1760aab0e986
Create Date: 2025-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_writing_styles'
down_revision: Union[str, None] = '1760aab0e986'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create writing_styles table
    op.create_table(
        'writing_styles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tone', sa.String(), nullable=True),
        sa.Column('formality_level', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('vocabulary_complexity', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('sample_texts', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('style_features', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_writing_styles_user_id'), 'writing_styles', ['user_id'], unique=False)
    op.create_index(op.f('ix_writing_styles_is_active'), 'writing_styles', ['is_active'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_writing_styles_is_active'), table_name='writing_styles')
    op.drop_index(op.f('ix_writing_styles_user_id'), table_name='writing_styles')

    # Drop table
    op.drop_table('writing_styles')
