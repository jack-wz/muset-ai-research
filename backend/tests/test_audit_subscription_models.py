"""
Tests for AuditLog and SubscriptionHistory Models

This module tests audit logging and subscription management functionality.
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Create a test base compatible with SQLite
TestBase = declarative_base()


# Simplified models for testing (SQLite compatible)
class TestUser(TestBase):
    """Test user model (SQLite compatible)."""

    __tablename__ = "test_users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    subscription_plan = Column(String, default="free", nullable=False)
    ai_chats_left = Column(Integer, default=50, nullable=False)
    ai_chats_total = Column(Integer, default=50, nullable=False)
    subscription_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestAuditLog(TestBase):
    """Test audit log model (SQLite compatible)."""

    __tablename__ = "test_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String, ForeignKey("test_users.id"), nullable=True)
    workspace_id = Column(String, nullable=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    payload = Column(JSON, default={})
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    metadata = Column(JSON, default={})
    status = Column(String, default="success", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestSubscriptionHistory(TestBase):
    """Test subscription history model (SQLite compatible)."""

    __tablename__ = "test_subscription_histories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("test_users.id"), nullable=False)
    previous_plan = Column(String, nullable=True)
    new_plan = Column(String, nullable=False)
    change_type = Column(String, nullable=False)
    amount_paid = Column(String, nullable=True)
    currency = Column(String, default="USD", nullable=False)
    payment_method = Column(String, nullable=True)
    transaction_id = Column(String, nullable=True)
    starts_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    previous_ai_chats_total = Column(Integer, nullable=True)
    new_ai_chats_total = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, default={})
    status = Column(String, default="active", nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
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


class TestAuditLogModel:
    """Test suite for AuditLog model."""

    def test_create_audit_log(self, test_session: Session):
        """Test creating an audit log entry."""
        # Create user first
        user = TestUser(
            email="test@example.com",
            name="Test User",
        )
        test_session.add(user)
        test_session.commit()

        # Create audit log
        log = TestAuditLog(
            actor_id=user.id,
            entity_type="page",
            entity_id=str(uuid.uuid4()),
            action="create",
            payload={"title": "New Page", "content": "Hello World"},
            ip_address="192.168.1.1",
        )

        test_session.add(log)
        test_session.commit()

        assert log.id is not None
        assert log.actor_id == user.id
        assert log.entity_type == "page"
        assert log.action == "create"
        assert log.status == "success"

    def test_audit_log_actions(self, test_session: Session):
        """Test different audit log actions."""
        user = TestUser(email="user@example.com", name="User")
        test_session.add(user)
        test_session.commit()

        actions = ["create", "update", "delete", "import", "export", "activate", "deactivate"]

        for action in actions:
            log = TestAuditLog(
                actor_id=user.id,
                entity_type="model",
                entity_id=str(uuid.uuid4()),
                action=action,
                payload={"test": "data"},
            )
            test_session.add(log)

        test_session.commit()

        # Verify all actions were created
        logs = test_session.query(TestAuditLog).all()
        assert len(logs) == len(actions)

    def test_audit_log_failed_action(self, test_session: Session):
        """Test audit log for failed action."""
        log = TestAuditLog(
            entity_type="file",
            entity_id=str(uuid.uuid4()),
            action="delete",
            payload={},
            status="failed",
            error_message="File not found",
        )

        test_session.add(log)
        test_session.commit()

        assert log.status == "failed"
        assert log.error_message == "File not found"

    def test_audit_log_with_workspace(self, test_session: Session):
        """Test audit log with workspace context."""
        workspace_id = str(uuid.uuid4())

        log = TestAuditLog(
            workspace_id=workspace_id,
            entity_type="page",
            entity_id=str(uuid.uuid4()),
            action="update",
            payload={"changes": ["title", "content"]},
        )

        test_session.add(log)
        test_session.commit()

        assert log.workspace_id == workspace_id

    def test_audit_log_query_by_entity(self, test_session: Session):
        """Test querying audit logs by entity."""
        entity_id = str(uuid.uuid4())

        # Create multiple logs for same entity
        for action in ["create", "update", "update", "delete"]:
            log = TestAuditLog(
                entity_type="page",
                entity_id=entity_id,
                action=action,
                payload={},
            )
            test_session.add(log)

        test_session.commit()

        # Query logs for this entity
        logs = test_session.query(TestAuditLog).filter_by(entity_id=entity_id).all()
        assert len(logs) == 4

    def test_audit_log_with_metadata(self, test_session: Session):
        """Test audit log with metadata."""
        log = TestAuditLog(
            entity_type="workspace",
            entity_id=str(uuid.uuid4()),
            action="create",
            payload={"name": "New Workspace"},
            metadata={
                "request_id": str(uuid.uuid4()),
                "client_version": "1.0.0",
                "platform": "web",
            },
        )

        test_session.add(log)
        test_session.commit()

        assert "request_id" in log.metadata
        assert log.metadata["platform"] == "web"


class TestSubscriptionHistoryModel:
    """Test suite for SubscriptionHistory model."""

    def test_create_subscription_history(self, test_session: Session):
        """Test creating a subscription history entry."""
        # Create user
        user = TestUser(
            email="subscriber@example.com",
            name="Subscriber",
        )
        test_session.add(user)
        test_session.commit()

        # Create subscription history
        history = TestSubscriptionHistory(
            user_id=user.id,
            previous_plan="free",
            new_plan="pro",
            change_type="upgrade",
            amount_paid="9.99",
            payment_method="stripe",
            transaction_id="txn_123456",
            starts_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            previous_ai_chats_total=50,
            new_ai_chats_total=500,
        )

        test_session.add(history)
        test_session.commit()

        assert history.id is not None
        assert history.user_id == user.id
        assert history.new_plan == "pro"
        assert history.change_type == "upgrade"

    def test_subscription_upgrade(self, test_session: Session):
        """Test subscription upgrade tracking."""
        user = TestUser(email="upgrader@example.com", name="Upgrader")
        test_session.add(user)
        test_session.commit()

        history = TestSubscriptionHistory(
            user_id=user.id,
            previous_plan="free",
            new_plan="pro",
            change_type="upgrade",
            amount_paid="9.99",
            starts_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            previous_ai_chats_total=50,
            new_ai_chats_total=500,
        )

        test_session.add(history)
        test_session.commit()

        assert history.change_type == "upgrade"
        assert history.new_ai_chats_total > history.previous_ai_chats_total

    def test_subscription_downgrade(self, test_session: Session):
        """Test subscription downgrade tracking."""
        user = TestUser(email="downgrader@example.com", name="Downgrader")
        test_session.add(user)
        test_session.commit()

        history = TestSubscriptionHistory(
            user_id=user.id,
            previous_plan="pro",
            new_plan="free",
            change_type="downgrade",
            starts_at=datetime.utcnow(),
            previous_ai_chats_total=500,
            new_ai_chats_total=50,
            notes="User requested downgrade",
        )

        test_session.add(history)
        test_session.commit()

        assert history.change_type == "downgrade"
        assert history.notes is not None

    def test_subscription_cancellation(self, test_session: Session):
        """Test subscription cancellation."""
        user = TestUser(email="canceller@example.com", name="Canceller")
        test_session.add(user)
        test_session.commit()

        history = TestSubscriptionHistory(
            user_id=user.id,
            previous_plan="pro",
            new_plan="free",
            change_type="cancellation",
            starts_at=datetime.utcnow(),
            previous_ai_chats_total=500,
            new_ai_chats_total=50,
            status="cancelled",
            cancelled_at=datetime.utcnow(),
            cancellation_reason="Too expensive",
        )

        test_session.add(history)
        test_session.commit()

        assert history.status == "cancelled"
        assert history.cancelled_at is not None
        assert history.cancellation_reason is not None

    def test_subscription_renewal(self, test_session: Session):
        """Test subscription renewal."""
        user = TestUser(email="renewer@example.com", name="Renewer")
        test_session.add(user)
        test_session.commit()

        history = TestSubscriptionHistory(
            user_id=user.id,
            previous_plan="pro",
            new_plan="pro",
            change_type="renewal",
            amount_paid="9.99",
            payment_method="stripe",
            transaction_id="txn_renewal_123",
            starts_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            previous_ai_chats_total=500,
            new_ai_chats_total=500,
        )

        test_session.add(history)
        test_session.commit()

        assert history.change_type == "renewal"
        assert history.previous_plan == history.new_plan

    def test_subscription_history_timeline(self, test_session: Session):
        """Test subscription history timeline."""
        user = TestUser(email="timeline@example.com", name="Timeline User")
        test_session.add(user)
        test_session.commit()

        # Create timeline of subscription changes
        changes = [
            ("free", "pro", "upgrade"),
            ("pro", "pro", "renewal"),
            ("pro", "pro", "renewal"),
            ("pro", "free", "downgrade"),
        ]

        for prev_plan, new_plan, change_type in changes:
            history = TestSubscriptionHistory(
                user_id=user.id,
                previous_plan=prev_plan,
                new_plan=new_plan,
                change_type=change_type,
                starts_at=datetime.utcnow(),
                previous_ai_chats_total=50 if prev_plan == "free" else 500,
                new_ai_chats_total=50 if new_plan == "free" else 500,
            )
            test_session.add(history)

        test_session.commit()

        # Query user's subscription history
        histories = (
            test_session.query(TestSubscriptionHistory)
            .filter_by(user_id=user.id)
            .order_by(TestSubscriptionHistory.created_at)
            .all()
        )

        assert len(histories) == 4
        assert histories[0].change_type == "upgrade"
        assert histories[-1].change_type == "downgrade"


class TestUserSubscriptionMethods:
    """Test suite for User subscription helper methods."""

    def test_user_is_pro(self, test_session: Session):
        """Test checking if user is pro."""
        pro_user = TestUser(
            email="pro@example.com",
            name="Pro User",
            subscription_plan="pro",
        )
        free_user = TestUser(
            email="free@example.com",
            name="Free User",
            subscription_plan="free",
        )

        test_session.add_all([pro_user, free_user])
        test_session.commit()

        # Note: These are model-level checks, not method checks
        assert pro_user.subscription_plan == "pro"
        assert free_user.subscription_plan == "free"

    def test_user_quota_management(self, test_session: Session):
        """Test user quota tracking."""
        user = TestUser(
            email="quota@example.com",
            name="Quota User",
            ai_chats_left=50,
            ai_chats_total=50,
        )

        test_session.add(user)
        test_session.commit()

        # Decrement quota
        user.ai_chats_left -= 1
        test_session.commit()

        assert user.ai_chats_left == 49

        # Reset quota
        user.ai_chats_left = user.ai_chats_total
        test_session.commit()

        assert user.ai_chats_left == 50

    def test_user_subscription_expiration(self, test_session: Session):
        """Test subscription expiration tracking."""
        # User with active subscription
        active_user = TestUser(
            email="active@example.com",
            name="Active User",
            subscription_plan="pro",
            subscription_expires_at=datetime.utcnow() + timedelta(days=30),
        )

        # User with expired subscription
        expired_user = TestUser(
            email="expired@example.com",
            name="Expired User",
            subscription_plan="pro",
            subscription_expires_at=datetime.utcnow() - timedelta(days=1),
        )

        test_session.add_all([active_user, expired_user])
        test_session.commit()

        # Check expiration
        assert active_user.subscription_expires_at > datetime.utcnow()
        assert expired_user.subscription_expires_at < datetime.utcnow()


class TestIntegration:
    """Test integration between audit and subscription models."""

    def test_subscription_change_with_audit(self, test_session: Session):
        """Test that subscription changes are audited."""
        # Create user
        user = TestUser(email="integration@example.com", name="Integration User")
        test_session.add(user)
        test_session.commit()

        # Create subscription change
        subscription = TestSubscriptionHistory(
            user_id=user.id,
            previous_plan="free",
            new_plan="pro",
            change_type="upgrade",
            amount_paid="9.99",
            starts_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            previous_ai_chats_total=50,
            new_ai_chats_total=500,
        )
        test_session.add(subscription)
        test_session.commit()

        # Create audit log for subscription change
        audit = TestAuditLog(
            actor_id=user.id,
            entity_type="subscription",
            entity_id=subscription.id,
            action="upgrade",
            payload={
                "previous_plan": "free",
                "new_plan": "pro",
                "amount_paid": "9.99",
            },
        )
        test_session.add(audit)
        test_session.commit()

        # Verify both records exist
        assert subscription.id is not None
        assert audit.entity_id == subscription.id
        assert audit.payload["new_plan"] == "pro"
