"""
Tests for Writing Style Customization

This module tests writing style management functionality.
Validates requirements 13.1-13.5.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.style import WritingStyle
from app.services.style_manager import StyleManager


class TestStyleManager:
    """Test suite for style manager."""

    @pytest.mark.asyncio
    async def test_create_style(self, test_db: AsyncSession):
        """
        Test: Create a new writing style.

        Validates requirement 13.1: Style configuration interface.
        """
        manager = StyleManager(test_db)

        style = await manager.create_style(
            user_id=1,
            name="Professional Style",
            description="Formal business writing",
            tone="professional",
            formality_level=8,
            vocabulary_complexity=7,
        )

        assert style.id is not None
        assert style.name == "Professional Style"
        assert style.tone == "professional"
        assert style.formality_level == 8
        assert style.vocabulary_complexity == 7

    @pytest.mark.asyncio
    async def test_analyze_samples(self, test_db: AsyncSession):
        """
        Test: Analyze sample texts for style features.

        Validates requirement 13.2: Style sample upload and analysis.
        """
        manager = StyleManager(test_db)

        sample_texts = [
            "This is a professional document. It uses formal language.",
            "We recommend following best practices. Please review carefully.",
        ]

        features = await manager.analyze_samples(sample_texts)

        assert "sample_count" in features
        assert "avg_length" in features
        assert "avg_word_count" in features
        assert features["sample_count"] == 2

    @pytest.mark.asyncio
    async def test_get_user_styles(self, test_db: AsyncSession):
        """
        Test: Get all styles for a user.

        Validates requirement 13.4: Style skill integration.
        """
        manager = StyleManager(test_db)

        # Create multiple styles
        style1 = await manager.create_style(
            user_id=1,
            name="Style 1",
            tone="formal",
        )

        style2 = await manager.create_style(
            user_id=1,
            name="Style 2",
            tone="casual",
        )

        styles = await manager.get_user_styles(user_id=1)

        assert len(styles) >= 2
        style_names = {s.name for s in styles}
        assert "Style 1" in style_names
        assert "Style 2" in style_names

    @pytest.mark.asyncio
    async def test_activate_style(self, test_db: AsyncSession):
        """
        Test: Activate a writing style.

        Validates requirement 13.5: Style switching.
        """
        manager = StyleManager(test_db)

        style1 = await manager.create_style(
            user_id=1,
            name="Style 1",
        )

        style2 = await manager.create_style(
            user_id=1,
            name="Style 2",
        )

        # Activate style2
        activated = await manager.activate_style(style2.id, user_id=1)

        assert activated.id == style2.id
        assert activated.is_active is True

        # Verify style1 is deactivated
        await test_db.refresh(style1)
        assert style1.is_active is False

        # Get active style
        active_style = await manager.get_active_style(user_id=1)
        assert active_style is not None
        assert active_style.id == style2.id

    @pytest.mark.asyncio
    async def test_delete_style(self, test_db: AsyncSession):
        """
        Test: Delete a writing style.
        """
        manager = StyleManager(test_db)

        style = await manager.create_style(
            user_id=1,
            name="To Delete",
        )

        style_id = style.id

        # Delete style
        await manager.delete_style(style_id, user_id=1)

        # Verify deleted
        styles = await manager.get_user_styles(user_id=1)
        style_ids = {s.id for s in styles}
        assert style_id not in style_ids

    @pytest.mark.asyncio
    async def test_cannot_delete_active_style(self, test_db: AsyncSession):
        """
        Test: Cannot delete active style.
        """
        manager = StyleManager(test_db)

        style = await manager.create_style(
            user_id=1,
            name="Active Style",
        )

        # Activate style
        await manager.activate_style(style.id, user_id=1)

        # Try to delete - should fail
        with pytest.raises(Exception):
            await manager.delete_style(style.id, user_id=1)

    @pytest.mark.asyncio
    async def test_build_style_prompt(self, test_db: AsyncSession):
        """
        Test: Build AI prompt from style configuration.

        Validates requirement 13.3: Style application logic.
        """
        manager = StyleManager(test_db)

        style = await manager.create_style(
            user_id=1,
            name="Casual Style",
            tone="casual",
            formality_level=3,
            vocabulary_complexity=4,
            sample_texts=["Hey there! This is pretty cool."],
        )

        prompt = manager.build_style_prompt(style)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "casual" in prompt.lower()

    @pytest.mark.asyncio
    async def test_formality_level_validation(self, test_db: AsyncSession):
        """
        Test: Formality level must be between 1 and 10.
        """
        manager = StyleManager(test_db)

        # Invalid formality level
        with pytest.raises(Exception):
            await manager.create_style(
                user_id=1,
                name="Invalid Style",
                formality_level=11,  # Invalid
            )

    @pytest.mark.asyncio
    async def test_style_with_samples(self, test_db: AsyncSession):
        """
        Test: Create style with sample texts.

        Validates requirement 13.2: Style sample upload.
        """
        manager = StyleManager(test_db)

        samples = [
            "This is an example of my writing style.",
            "I tend to use short sentences. Clear and concise.",
            "Sometimes I add a question? For variety.",
        ]

        style = await manager.create_style(
            user_id=1,
            name="My Style",
            sample_texts=samples,
        )

        assert style.sample_texts == samples
        assert style.style_features is not None
        assert "sample_count" in style.style_features
        assert style.style_features["sample_count"] == 3
