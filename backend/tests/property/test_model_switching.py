"""
Property Test: Model Switching Correctness (Property 12)

This test verifies that when switching between different AI models,
subsequent requests use the correct model with proper configurations.

Validates Requirement 20.4: Model switching logic
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import ModelConfig
from app.services.model_config_manager import ModelConfigManager


@pytest.fixture
async def db_session() -> AsyncSession:
    """Create async database session for testing."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create tables
        from app.db.base import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield session


@pytest.mark.asyncio
@given(
    provider=st.sampled_from(["anthropic", "openai", "local"]),
    model_name=st.text(
        min_size=3,
        max_size=30,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_."),
    ),
)
@settings(max_examples=30, deadline=5000)
async def test_model_switch_updates_current_model(
    db_session: AsyncSession, provider: str, model_name: str
) -> None:
    """
    Property Test: Switching models updates the current model instance.

    Tests that when switching to a different model configuration,
    the manager's current model is updated correctly.

    Args:
        db_session: Database session
        provider: Model provider
        model_name: Model name
    """
    manager = ModelConfigManager(db_session)

    # Create a model configuration
    config = ModelConfig(
        provider=provider,
        label=f"Test {provider} model",
        model_name=model_name,
        is_default=True,
        capabilities={
            "streaming": True,
            "vision": False,
            "toolUse": True,
            "multilingual": True,
        },
    )

    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    # Mock the model creation to avoid actual API calls
    with patch.object(manager, "_create_model_instance") as mock_create:
        mock_model = MagicMock()
        mock_model.model_name = model_name
        mock_create.return_value = mock_model

        # Switch to the model
        result = await manager.switch_model(config_id=config.id)

        # Verify current model was updated
        assert manager.current_model is not None
        assert manager.current_model.model_name == model_name
        assert manager.current_config == config


@pytest.mark.asyncio
async def test_multiple_model_switches_consistency(db_session: AsyncSession) -> None:
    """
    Integration Test: Multiple model switches maintain consistency.

    Tests that switching between multiple models multiple times
    always results in the correct current model.
    """
    manager = ModelConfigManager(db_session)

    # Create multiple configurations
    configs = []
    for i, provider in enumerate(["anthropic", "openai", "local"]):
        config = ModelConfig(
            provider=provider,
            label=f"Model {i}",
            model_name=f"model-{i}",
            is_default=(i == 0),
            capabilities={"streaming": True},
        )
        db_session.add(config)
        configs.append(config)

    await db_session.commit()

    # Mock model creation
    with patch.object(manager, "_create_model_instance") as mock_create:

        def create_mock_model(config: ModelConfig) -> MagicMock:
            mock = MagicMock()
            mock.model_name = config.model_name
            return mock

        mock_create.side_effect = create_mock_model

        # Switch between models multiple times
        for _ in range(3):
            for config in configs:
                await manager.switch_model(config_id=config.id)

                # Verify current model is correct
                assert manager.current_model is not None
                assert manager.current_model.model_name == config.model_name
                assert manager.current_config.id == config.id


@pytest.mark.asyncio
async def test_model_switch_applies_correct_parameters(db_session: AsyncSession) -> None:
    """
    Integration Test: Model switching applies correct parameters.

    Tests that when switching models, the correct parameters
    (API keys, base URLs, etc.) are applied.
    """
    manager = ModelConfigManager(db_session)

    # Create configuration with specific parameters
    config = ModelConfig(
        provider="anthropic",
        label="Test Anthropic",
        model_name="claude-3-sonnet-20240229",
        base_url="https://custom-api.example.com",
        is_default=True,
        capabilities={"streaming": True, "toolUse": True},
    )

    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    # Mock ChatAnthropic to capture initialization parameters
    with patch("app.services.model_config_manager.ChatAnthropic") as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance

        await manager.switch_model(config_id=config.id)

        # Verify ChatAnthropic was called with correct parameters
        mock_chat.assert_called_once()
        call_kwargs = mock_chat.call_args.kwargs

        assert call_kwargs["model"] == "claude-3-sonnet-20240229"
        assert call_kwargs["base_url"] == "https://custom-api.example.com"
        assert call_kwargs["streaming"] is True


@pytest.mark.asyncio
async def test_model_switch_by_label(db_session: AsyncSession) -> None:
    """
    Integration Test: Can switch models by label.

    Tests that models can be switched using their label
    instead of ID.
    """
    manager = ModelConfigManager(db_session)

    label = "My Custom Model"
    config = ModelConfig(
        provider="openai",
        label=label,
        model_name="gpt-4",
        is_default=True,
    )

    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    with patch.object(manager, "_create_model_instance") as mock_create:
        mock_model = MagicMock()
        mock_create.return_value = mock_model

        # Switch by label
        await manager.switch_model(label=label)

        # Verify correct model was loaded
        assert manager.current_config.label == label


@pytest.mark.asyncio
async def test_model_switch_to_default_when_no_params(db_session: AsyncSession) -> None:
    """
    Integration Test: Switches to default model when no parameters provided.

    Tests that when switch_model is called without specifying config_id
    or label, it loads the default model.
    """
    manager = ModelConfigManager(db_session)

    # Create non-default model
    config1 = ModelConfig(
        provider="openai",
        label="Non-default",
        model_name="gpt-3.5-turbo",
        is_default=False,
    )

    # Create default model
    config2 = ModelConfig(
        provider="anthropic",
        label="Default",
        model_name="claude-3-opus-20240229",
        is_default=True,
    )

    db_session.add_all([config1, config2])
    await db_session.commit()

    with patch.object(manager, "_create_model_instance") as mock_create:
        mock_model = MagicMock()
        mock_create.return_value = mock_model

        # Switch without parameters
        await manager.switch_model()

        # Verify default model was loaded
        assert manager.current_config.is_default is True
        assert manager.current_config.label == "Default"


@pytest.mark.asyncio
async def test_model_switch_nonexistent_model_fails(db_session: AsyncSession) -> None:
    """
    Integration Test: Switching to nonexistent model fails gracefully.

    Tests that attempting to switch to a non-existent model
    raises an appropriate error.
    """
    from app.core.exceptions import ValidationError

    manager = ModelConfigManager(db_session)

    with pytest.raises(ValidationError, match="not found"):
        await manager.switch_model(config_id=99999)


@pytest.mark.asyncio
@given(
    streaming=st.booleans(),
    vision=st.booleans(),
    tool_use=st.booleans(),
)
@settings(max_examples=20, deadline=5000)
async def test_model_capabilities_preserved_after_switch(
    db_session: AsyncSession, streaming: bool, vision: bool, tool_use: bool
) -> None:
    """
    Property Test: Model capabilities are preserved after switching.

    Tests that when switching models, the capability settings
    are correctly applied to the new model instance.

    Args:
        db_session: Database session
        streaming: Streaming capability
        vision: Vision capability
        tool_use: Tool use capability
    """
    manager = ModelConfigManager(db_session)

    capabilities = {
        "streaming": streaming,
        "vision": vision,
        "toolUse": tool_use,
        "multilingual": True,
    }

    config = ModelConfig(
        provider="anthropic",
        label="Capability Test",
        model_name="claude-3-sonnet-20240229",
        is_default=True,
        capabilities=capabilities,
    )

    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    with patch("app.services.model_config_manager.ChatAnthropic") as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance

        await manager.switch_model(config_id=config.id)

        # Verify streaming capability was applied
        call_kwargs = mock_chat.call_args.kwargs
        assert call_kwargs["streaming"] == streaming


@pytest.mark.asyncio
async def test_concurrent_model_switches(db_session: AsyncSession) -> None:
    """
    Integration Test: Concurrent model switches are handled correctly.

    Tests that if multiple model switches are requested concurrently,
    the final state is consistent.
    """
    import asyncio

    manager = ModelConfigManager(db_session)

    # Create multiple configurations
    configs = []
    for i in range(5):
        config = ModelConfig(
            provider="anthropic",
            label=f"Model {i}",
            model_name=f"claude-{i}",
            is_default=(i == 0),
        )
        db_session.add(config)
        configs.append(config)

    await db_session.commit()

    with patch.object(manager, "_create_model_instance") as mock_create:

        def create_mock(config: ModelConfig) -> MagicMock:
            mock = MagicMock()
            mock.model_name = config.model_name
            return mock

        mock_create.side_effect = create_mock

        # Trigger multiple switches concurrently
        tasks = [manager.switch_model(config_id=config.id) for config in configs]
        await asyncio.gather(*tasks)

        # Verify final state is one of the configs
        assert manager.current_model is not None
        assert any(
            manager.current_model.model_name == config.model_name for config in configs
        )
