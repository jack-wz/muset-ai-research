"""Add AuditLog and SubscriptionHistory models

Revision ID: add_audit_subscription
Revises: add_upload_agent
Create Date: 2025-01-19 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_audit_subscription'
down_revision: Union[str, None] = 'add_upload_agent'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create AuditLog and SubscriptionHistory tables."""

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'actor_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            'workspace_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            'entity_type',
            sa.String(),
            nullable=False,
            comment='Type of entity: page, file, model, skill, workspace, user, etc.'
        ),
        sa.Column(
            'entity_id',
            sa.String(),
            nullable=False,
            comment='ID of the entity being acted upon'
        ),
        sa.Column(
            'action',
            sa.String(),
            nullable=False,
            comment='Action: create, update, delete, import, export, activate, deactivate'
        ),
        sa.Column(
            'payload',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='{}',
            comment='Detailed action payload'
        ),
        sa.Column(
            'ip_address',
            sa.String(),
            nullable=True,
            comment='IP address of the request'
        ),
        sa.Column(
            'user_agent',
            sa.String(),
            nullable=True,
            comment='User agent string'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default='{}',
            comment='Additional metadata'
        ),
        sa.Column(
            'status',
            sa.String(),
            nullable=False,
            server_default='success',
            comment='Status: success, failed, partial'
        ),
        sa.Column(
            'error_message',
            sa.Text(),
            nullable=True,
            comment='Error message if action failed'
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
            ['actor_id'],
            ['users.id'],
            ondelete='SET NULL'
        ),
        sa.ForeignKeyConstraint(
            ['workspace_id'],
            ['workspaces.id'],
            ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for audit_logs
    op.create_index(
        op.f('ix_audit_logs_actor_id'),
        'audit_logs',
        ['actor_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_audit_logs_workspace_id'),
        'audit_logs',
        ['workspace_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_audit_logs_entity_type'),
        'audit_logs',
        ['entity_type'],
        unique=False
    )
    op.create_index(
        op.f('ix_audit_logs_entity_id'),
        'audit_logs',
        ['entity_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_audit_logs_action'),
        'audit_logs',
        ['action'],
        unique=False
    )
    op.create_index(
        op.f('ix_audit_logs_created_at'),
        'audit_logs',
        ['created_at'],
        unique=False
    )

    # Create subscription_histories table
    op.create_table(
        'subscription_histories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            'previous_plan',
            sa.String(),
            nullable=True,
            comment='Previous subscription plan'
        ),
        sa.Column(
            'new_plan',
            sa.String(),
            nullable=False,
            comment='New subscription plan: free, pro'
        ),
        sa.Column(
            'change_type',
            sa.String(),
            nullable=False,
            comment='Change type: upgrade, downgrade, renewal, cancellation, expiration'
        ),
        sa.Column(
            'amount_paid',
            sa.String(),
            nullable=True,
            comment='Amount paid'
        ),
        sa.Column(
            'currency',
            sa.String(),
            nullable=False,
            server_default='USD',
            comment='Currency code'
        ),
        sa.Column(
            'payment_method',
            sa.String(),
            nullable=True,
            comment='Payment method used'
        ),
        sa.Column(
            'transaction_id',
            sa.String(),
            nullable=True,
            comment='External payment transaction ID'
        ),
        sa.Column(
            'starts_at',
            sa.DateTime(timezone=True),
            nullable=False,
            comment='Subscription start date'
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Subscription expiration date'
        ),
        sa.Column(
            'previous_ai_chats_total',
            sa.Integer(),
            nullable=True,
            comment='Previous AI chat quota'
        ),
        sa.Column(
            'new_ai_chats_total',
            sa.Integer(),
            nullable=False,
            comment='New AI chat quota'
        ),
        sa.Column(
            'notes',
            sa.Text(),
            nullable=True,
            comment='Additional notes about this change'
        ),
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default='{}',
            comment='Additional metadata'
        ),
        sa.Column(
            'status',
            sa.String(),
            nullable=False,
            server_default='active',
            comment='Status: active, cancelled, expired, pending'
        ),
        sa.Column(
            'cancelled_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Cancellation date'
        ),
        sa.Column(
            'cancellation_reason',
            sa.Text(),
            nullable=True,
            comment='Reason for cancellation'
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
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for subscription_histories
    op.create_index(
        op.f('ix_subscription_histories_user_id'),
        'subscription_histories',
        ['user_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_subscription_histories_change_type'),
        'subscription_histories',
        ['change_type'],
        unique=False
    )
    op.create_index(
        op.f('ix_subscription_histories_transaction_id'),
        'subscription_histories',
        ['transaction_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_subscription_histories_created_at'),
        'subscription_histories',
        ['created_at'],
        unique=False
    )


def downgrade() -> None:
    """Drop AuditLog and SubscriptionHistory tables."""

    # Drop subscription_histories table
    op.drop_index(
        op.f('ix_subscription_histories_created_at'),
        table_name='subscription_histories'
    )
    op.drop_index(
        op.f('ix_subscription_histories_transaction_id'),
        table_name='subscription_histories'
    )
    op.drop_index(
        op.f('ix_subscription_histories_change_type'),
        table_name='subscription_histories'
    )
    op.drop_index(
        op.f('ix_subscription_histories_user_id'),
        table_name='subscription_histories'
    )
    op.drop_table('subscription_histories')

    # Drop audit_logs table
    op.drop_index(
        op.f('ix_audit_logs_created_at'),
        table_name='audit_logs'
    )
    op.drop_index(
        op.f('ix_audit_logs_action'),
        table_name='audit_logs'
    )
    op.drop_index(
        op.f('ix_audit_logs_entity_id'),
        table_name='audit_logs'
    )
    op.drop_index(
        op.f('ix_audit_logs_entity_type'),
        table_name='audit_logs'
    )
    op.drop_index(
        op.f('ix_audit_logs_workspace_id'),
        table_name='audit_logs'
    )
    op.drop_index(
        op.f('ix_audit_logs_actor_id'),
        table_name='audit_logs'
    )
    op.drop_table('audit_logs')
