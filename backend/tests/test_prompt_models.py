"""
Tests for PromptSuggestion and InspirationBoard Models

This module tests the prompt suggestion and inspiration board functionality.
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Create a test base compatible with SQLite
TestBase = declarative_base()


# Simplified models for testing (SQLite compatible)
class TestPromptSuggestion(TestBase):
    """Test prompt suggestion model (SQLite compatible)."""

    __tablename__ = "prompt_suggestions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    icon = Column(String, nullable=True)
    tags = Column(JSON, default=[])
    locale = Column(String, default="en", nullable=False)
    required_skills = Column(JSON, default=[])
    usage_count = Column(String, default="0", nullable=False)
    rating = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestInspirationBoard(TestBase):
    """Test inspiration board model (SQLite compatible)."""

    __tablename__ = "inspiration_boards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    related_page_ids = Column(JSON, default=[])
    suggestions = Column(JSON, default=[])
    community_sample_ids = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)
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


class TestPromptSuggestionModel:
    """Test suite for PromptSuggestion model."""

    def test_create_prompt_suggestion(self, test_session: Session):
        """Test creating a prompt suggestion."""
        suggestion = TestPromptSuggestion(
            category="question",
            text="What are the main themes in your story?",
            icon="❓",
            tags=["writing", "story", "theme"],
            locale="en",
        )

        test_session.add(suggestion)
        test_session.commit()

        assert suggestion.id is not None
        assert suggestion.category == "question"
        assert suggestion.text == "What are the main themes in your story?"
        assert suggestion.icon == "❓"
        assert suggestion.tags == ["writing", "story", "theme"]
        assert suggestion.locale == "en"
        assert suggestion.usage_count == "0"
        assert suggestion.created_at is not None

    def test_create_prompt_suggestion_with_skills(self, test_session: Session):
        """Test creating a prompt suggestion with required skills."""
        suggestion = TestPromptSuggestion(
            category="theme",
            text="Develop a character arc",
            tags=["character", "development"],
            locale="en",
            required_skills=["character-analysis", "narrative-structure"],
        )

        test_session.add(suggestion)
        test_session.commit()

        assert suggestion.required_skills == ["character-analysis", "narrative-structure"]

    def test_prompt_suggestion_categories(self, test_session: Session):
        """Test creating suggestions with different categories."""
        categories = ["question", "theme", "angle", "community-sample"]

        for category in categories:
            suggestion = TestPromptSuggestion(
                category=category,
                text=f"Test suggestion for {category}",
                locale="en",
            )
            test_session.add(suggestion)

        test_session.commit()

        # Query all suggestions
        suggestions = test_session.query(TestPromptSuggestion).all()
        assert len(suggestions) == len(categories)

        # Verify categories
        retrieved_categories = [s.category for s in suggestions]
        assert set(retrieved_categories) == set(categories)

    def test_prompt_suggestion_locale_filtering(self, test_session: Session):
        """Test filtering suggestions by locale."""
        # Create suggestions in different locales
        en_suggestion = TestPromptSuggestion(
            category="question",
            text="What is your story about?",
            locale="en",
        )
        zh_suggestion = TestPromptSuggestion(
            category="question",
            text="你的故事是关于什么的？",
            locale="zh",
        )

        test_session.add_all([en_suggestion, zh_suggestion])
        test_session.commit()

        # Query English suggestions
        en_suggestions = (
            test_session.query(TestPromptSuggestion)
            .filter(TestPromptSuggestion.locale == "en")
            .all()
        )
        assert len(en_suggestions) == 1
        assert en_suggestions[0].text == "What is your story about?"

        # Query Chinese suggestions
        zh_suggestions = (
            test_session.query(TestPromptSuggestion)
            .filter(TestPromptSuggestion.locale == "zh")
            .all()
        )
        assert len(zh_suggestions) == 1
        assert zh_suggestions[0].text == "你的故事是关于什么的？"

    def test_prompt_suggestion_tag_filtering(self, test_session: Session):
        """Test filtering suggestions by tags."""
        suggestion1 = TestPromptSuggestion(
            category="question",
            text="Suggestion 1",
            tags=["writing", "creative"],
            locale="en",
        )
        suggestion2 = TestPromptSuggestion(
            category="theme",
            text="Suggestion 2",
            tags=["technical", "analysis"],
            locale="en",
        )

        test_session.add_all([suggestion1, suggestion2])
        test_session.commit()

        # Note: SQLite JSON filtering is limited, so we'll test in Python
        all_suggestions = test_session.query(TestPromptSuggestion).all()
        writing_suggestions = [s for s in all_suggestions if "writing" in s.tags]

        assert len(writing_suggestions) == 1
        assert writing_suggestions[0].text == "Suggestion 1"

    def test_prompt_suggestion_usage_tracking(self, test_session: Session):
        """Test tracking suggestion usage count."""
        suggestion = TestPromptSuggestion(
            category="question",
            text="Test suggestion",
            locale="en",
            usage_count="0",
        )

        test_session.add(suggestion)
        test_session.commit()

        # Simulate usage
        suggestion.usage_count = "5"
        test_session.commit()

        # Retrieve and verify
        retrieved = test_session.query(TestPromptSuggestion).filter_by(id=suggestion.id).first()
        assert retrieved.usage_count == "5"


class TestInspirationBoardModel:
    """Test suite for InspirationBoard model."""

    def test_create_inspiration_board(self, test_session: Session):
        """Test creating an inspiration board."""
        workspace_id = str(uuid.uuid4())
        board = TestInspirationBoard(
            workspace_id=workspace_id,
            title="My Story Ideas",
            description="Collection of ideas for my novel",
        )

        test_session.add(board)
        test_session.commit()

        assert board.id is not None
        assert board.workspace_id == workspace_id
        assert board.title == "My Story Ideas"
        assert board.description == "Collection of ideas for my novel"
        assert board.status == "active"
        assert board.created_at is not None

    def test_inspiration_board_with_suggestions(self, test_session: Session):
        """Test creating an inspiration board with prompt suggestions."""
        # Create prompt suggestions first
        suggestion1 = TestPromptSuggestion(
            category="theme",
            text="Explore the hero's journey",
            locale="en",
        )
        suggestion2 = TestPromptSuggestion(
            category="angle",
            text="Tell the story from the villain's perspective",
            locale="en",
        )

        test_session.add_all([suggestion1, suggestion2])
        test_session.commit()

        # Create inspiration board with suggestions
        board = TestInspirationBoard(
            workspace_id=str(uuid.uuid4()),
            title="Character Development",
            suggestions=[suggestion1.id, suggestion2.id],
        )

        test_session.add(board)
        test_session.commit()

        assert len(board.suggestions) == 2
        assert suggestion1.id in board.suggestions
        assert suggestion2.id in board.suggestions

    def test_inspiration_board_with_pages(self, test_session: Session):
        """Test creating an inspiration board with related pages."""
        page_id1 = str(uuid.uuid4())
        page_id2 = str(uuid.uuid4())

        board = TestInspirationBoard(
            workspace_id=str(uuid.uuid4()),
            title="Novel Outline",
            related_page_ids=[page_id1, page_id2],
        )

        test_session.add(board)
        test_session.commit()

        assert len(board.related_page_ids) == 2
        assert page_id1 in board.related_page_ids
        assert page_id2 in board.related_page_ids

    def test_inspiration_board_with_community_samples(self, test_session: Session):
        """Test creating an inspiration board with community samples."""
        board = TestInspirationBoard(
            workspace_id=str(uuid.uuid4()),
            title="Writing Examples",
            community_sample_ids=["sample-1", "sample-2", "sample-3"],
        )

        test_session.add(board)
        test_session.commit()

        assert len(board.community_sample_ids) == 3
        assert "sample-1" in board.community_sample_ids

    def test_inspiration_board_status_change(self, test_session: Session):
        """Test changing inspiration board status."""
        board = TestInspirationBoard(
            workspace_id=str(uuid.uuid4()),
            title="Active Board",
            status="active",
        )

        test_session.add(board)
        test_session.commit()

        # Archive the board
        board.status = "archived"
        test_session.commit()

        # Retrieve and verify
        retrieved = test_session.query(TestInspirationBoard).filter_by(id=board.id).first()
        assert retrieved.status == "archived"

    def test_inspiration_board_workspace_filtering(self, test_session: Session):
        """Test filtering inspiration boards by workspace."""
        workspace1_id = str(uuid.uuid4())
        workspace2_id = str(uuid.uuid4())

        board1 = TestInspirationBoard(
            workspace_id=workspace1_id,
            title="Workspace 1 Board",
        )
        board2 = TestInspirationBoard(
            workspace_id=workspace2_id,
            title="Workspace 2 Board",
        )

        test_session.add_all([board1, board2])
        test_session.commit()

        # Query boards for workspace 1
        workspace1_boards = (
            test_session.query(TestInspirationBoard)
            .filter(TestInspirationBoard.workspace_id == workspace1_id)
            .all()
        )

        assert len(workspace1_boards) == 1
        assert workspace1_boards[0].title == "Workspace 1 Board"

    def test_inspiration_board_notes(self, test_session: Session):
        """Test adding notes to inspiration board."""
        board = TestInspirationBoard(
            workspace_id=str(uuid.uuid4()),
            title="Research Notes",
            notes="These are my research notes for the fantasy novel.",
        )

        test_session.add(board)
        test_session.commit()

        assert board.notes == "These are my research notes for the fantasy novel."

        # Update notes
        board.notes = "Updated research notes with new ideas."
        test_session.commit()

        retrieved = test_session.query(TestInspirationBoard).filter_by(id=board.id).first()
        assert retrieved.notes == "Updated research notes with new ideas."


class TestPromptSuggestionAndInspirationIntegration:
    """Test integration between PromptSuggestion and InspirationBoard."""

    def test_collect_suggestions_into_board(self, test_session: Session):
        """Test collecting multiple suggestions into an inspiration board."""
        # Create several prompt suggestions
        suggestions = [
            TestPromptSuggestion(
                category="question",
                text=f"Question {i}",
                locale="en",
            )
            for i in range(5)
        ]

        test_session.add_all(suggestions)
        test_session.commit()

        # Create board with all suggestions
        board = TestInspirationBoard(
            workspace_id=str(uuid.uuid4()),
            title="All Questions",
            suggestions=[s.id for s in suggestions],
        )

        test_session.add(board)
        test_session.commit()

        assert len(board.suggestions) == 5

    def test_filter_suggestions_by_category_and_add_to_board(self, test_session: Session):
        """Test filtering suggestions by category and adding to board."""
        # Create suggestions with different categories
        question_sugg = TestPromptSuggestion(
            category="question",
            text="What is the main conflict?",
            locale="en",
        )
        theme_sugg = TestPromptSuggestion(
            category="theme",
            text="Explore redemption",
            locale="en",
        )

        test_session.add_all([question_sugg, theme_sugg])
        test_session.commit()

        # Query only theme suggestions
        theme_suggestions = (
            test_session.query(TestPromptSuggestion)
            .filter(TestPromptSuggestion.category == "theme")
            .all()
        )

        # Create board with only theme suggestions
        board = TestInspirationBoard(
            workspace_id=str(uuid.uuid4()),
            title="Themes Collection",
            suggestions=[s.id for s in theme_suggestions],
        )

        test_session.add(board)
        test_session.commit()

        assert len(board.suggestions) == 1
        assert theme_sugg.id in board.suggestions
        assert question_sugg.id not in board.suggestions
