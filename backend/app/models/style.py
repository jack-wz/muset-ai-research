"""Writing style models."""
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base
from app.models.mixins import BaseMixin


class WritingStyle(Base, BaseMixin):
    """Writing style configuration."""

    __tablename__ = "writing_styles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Style parameters
    tone = Column(String, nullable=True)  # formal, casual, professional, friendly
    formality_level = Column(Integer, default=5, nullable=False)  # 1-10 scale
    vocabulary_complexity = Column(
        Integer, default=5, nullable=False
    )  # 1-10 scale

    # Example samples for style learning
    sample_texts = Column(JSONB, default=[], nullable=False)

    # Extracted style features
    style_features = Column(JSONB, nullable=True)

    # Is this the active style?
    is_active = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<WritingStyle {self.name}>"
