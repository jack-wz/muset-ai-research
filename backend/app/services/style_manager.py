"""
Writing Style Management Service

This module provides functionality to manage writing styles,
including analyzing sample texts and applying styles to content generation.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models.style import WritingStyle

logger = logging.getLogger(__name__)


class StyleManager:
    """
    Manager for writing styles.

    This class handles creation, analysis, and application of writing styles.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the style manager.

        Args:
            db: Database session
        """
        self.db = db

    async def create_style(
        self,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        tone: Optional[str] = None,
        formality_level: int = 5,
        vocabulary_complexity: int = 5,
        sample_texts: Optional[List[str]] = None,
    ) -> WritingStyle:
        """
        Create a new writing style.

        Args:
            user_id: User ID
            name: Style name
            description: Style description
            tone: Tone (formal, casual, professional, friendly)
            formality_level: Formality level (1-10)
            vocabulary_complexity: Vocabulary complexity (1-10)
            sample_texts: Sample texts for style learning

        Returns:
            Created style

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate parameters
            if formality_level < 1 or formality_level > 10:
                raise ValidationError("Formality level must be between 1 and 10")

            if vocabulary_complexity < 1 or vocabulary_complexity > 10:
                raise ValidationError(
                    "Vocabulary complexity must be between 1 and 10"
                )

            # Analyze samples if provided
            style_features = None
            if sample_texts:
                style_features = await self.analyze_samples(sample_texts)

            # Create style
            style = WritingStyle(
                user_id=user_id,
                name=name,
                description=description,
                tone=tone,
                formality_level=formality_level,
                vocabulary_complexity=vocabulary_complexity,
                sample_texts=sample_texts or [],
                style_features=style_features,
                is_active=False,
            )

            self.db.add(style)
            await self.db.commit()
            await self.db.refresh(style)

            logger.info(f"Created writing style: {name} for user {user_id}")

            return style

        except ValidationError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create writing style: {str(e)}")
            raise ValidationError(f"Style creation failed: {str(e)}")

    async def analyze_samples(self, sample_texts: List[str]) -> Dict[str, Any]:
        """
        Analyze sample texts to extract style features.

        Args:
            sample_texts: List of sample texts

        Returns:
            Dictionary of style features

        Note:
            This is a simplified implementation. In production, this would
            use NLP techniques to analyze writing patterns.
        """
        if not sample_texts:
            return {}

        # Simple analysis (placeholder for real NLP analysis)
        features = {
            "sample_count": len(sample_texts),
            "avg_length": sum(len(text) for text in sample_texts) / len(sample_texts),
            "avg_word_count": sum(
                len(text.split()) for text in sample_texts
            ) / len(sample_texts),
            # In production, add more sophisticated features:
            # - Sentence structure patterns
            # - Vocabulary richness
            # - Punctuation patterns
            # - Paragraph organization
        }

        return features

    async def get_user_styles(self, user_id: int) -> List[WritingStyle]:
        """
        Get all writing styles for a user.

        Args:
            user_id: User ID

        Returns:
            List of writing styles
        """
        result = await self.db.execute(
            select(WritingStyle).where(WritingStyle.user_id == user_id)
        )
        styles = result.scalars().all()

        return list(styles)

    async def get_active_style(self, user_id: int) -> Optional[WritingStyle]:
        """
        Get the active writing style for a user.

        Args:
            user_id: User ID

        Returns:
            Active style or None
        """
        result = await self.db.execute(
            select(WritingStyle).where(
                WritingStyle.user_id == user_id, WritingStyle.is_active == True
            )
        )
        style = result.scalar_one_or_none()

        return style

    async def activate_style(self, style_id: int, user_id: int) -> WritingStyle:
        """
        Activate a writing style (deactivates others).

        Args:
            style_id: Style ID
            user_id: User ID

        Returns:
            Activated style

        Raises:
            ValidationError: If style not found
        """
        # Deactivate all styles for user
        result = await self.db.execute(
            select(WritingStyle).where(WritingStyle.user_id == user_id)
        )
        all_styles = result.scalars().all()

        for style in all_styles:
            style.is_active = False

        # Activate the specified style
        result = await self.db.execute(
            select(WritingStyle).where(
                WritingStyle.id == style_id, WritingStyle.user_id == user_id
            )
        )
        style = result.scalar_one_or_none()

        if not style:
            raise ValidationError(f"Style {style_id} not found")

        style.is_active = True

        await self.db.commit()
        await self.db.refresh(style)

        logger.info(f"Activated writing style: {style.name} for user {user_id}")

        return style

    async def delete_style(self, style_id: int, user_id: int) -> None:
        """
        Delete a writing style.

        Args:
            style_id: Style ID
            user_id: User ID

        Raises:
            ValidationError: If style not found or is active
        """
        result = await self.db.execute(
            select(WritingStyle).where(
                WritingStyle.id == style_id, WritingStyle.user_id == user_id
            )
        )
        style = result.scalar_one_or_none()

        if not style:
            raise ValidationError(f"Style {style_id} not found")

        if style.is_active:
            raise ValidationError("Cannot delete active style")

        await self.db.delete(style)
        await self.db.commit()

        logger.info(f"Deleted writing style: {style.name}")

    def build_style_prompt(self, style: WritingStyle) -> str:
        """
        Build a prompt that describes the writing style.

        Args:
            style: Writing style

        Returns:
            Style prompt for AI model

        Note:
            This prompt is used to guide the AI model to generate
            content in the specified style.
        """
        prompt_parts = []

        if style.tone:
            prompt_parts.append(f"Write in a {style.tone} tone.")

        if style.formality_level:
            if style.formality_level <= 3:
                prompt_parts.append("Use casual, conversational language.")
            elif style.formality_level >= 7:
                prompt_parts.append("Use formal, professional language.")
            else:
                prompt_parts.append("Use a balanced, semi-formal tone.")

        if style.vocabulary_complexity:
            if style.vocabulary_complexity <= 3:
                prompt_parts.append("Use simple, everyday vocabulary.")
            elif style.vocabulary_complexity >= 7:
                prompt_parts.append("Use sophisticated, varied vocabulary.")
            else:
                prompt_parts.append("Use clear, accessible language.")

        if style.sample_texts:
            prompt_parts.append(
                f"Emulate the writing style of these examples:\\n"
                f"{chr(10).join(style.sample_texts[:2])}"
            )

        return " ".join(prompt_parts)
