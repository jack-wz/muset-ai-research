"""
Model Configuration Management Service

This module provides functionality to manage AI model configurations,
including support for multiple providers (Anthropic, OpenAI, local models, etc.)
and model switching capabilities.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.security import encrypt_api_key, decrypt_api_key
from app.models.config import ModelConfig

logger = logging.getLogger(__name__)


class ModelConfigManager:
    """
    Manager for AI model configurations.

    This class handles configuration, switching, and management of
    different AI model providers.

    Attributes:
        db: Database session
        current_model: Currently active model instance
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the model config manager.

        Args:
            db: Database session
        """
        self.db = db
        self.current_model: Optional[BaseChatModel] = None
        self.current_config: Optional[ModelConfig] = None

    async def load_configurations(self) -> List[ModelConfig]:
        """
        Load all model configurations from database.

        Returns:
            List of model configurations
        """
        try:
            result = await self.db.execute(select(ModelConfig))
            configs = result.scalars().all()

            logger.info(f"Loaded {len(configs)} model configurations")
            return list(configs)

        except Exception as e:
            logger.error(f"Failed to load model configurations: {str(e)}")
            raise ValidationError(f"Configuration load failed: {str(e)}")

    async def get_default_configuration(self) -> Optional[ModelConfig]:
        """
        Get the default model configuration.

        Returns:
            Default configuration or None
        """
        try:
            result = await self.db.execute(
                select(ModelConfig).where(ModelConfig.is_default == True)
            )
            config = result.scalar_one_or_none()

            return config

        except Exception as e:
            logger.error(f"Failed to get default configuration: {str(e)}")
            return None

    async def save_configuration(
        self,
        provider: str,
        label: str,
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        is_default: bool = False,
        capabilities: Optional[Dict[str, Any]] = None,
        guardrails: Optional[Dict[str, Any]] = None,
    ) -> ModelConfig:
        """
        Save a new model configuration.

        Args:
            provider: Model provider (anthropic, openai, etc.)
            label: Human-readable label
            model_name: Model identifier
            api_key: Optional API key (will be encrypted)
            base_url: Optional base URL for custom endpoints
            is_default: Whether this is the default model
            capabilities: Model capabilities dict
            guardrails: Model guardrails dict

        Returns:
            Saved configuration

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate provider
            valid_providers = ["anthropic", "openai", "azure", "local", "doubao", "qianwen", "kimi"]
            if provider not in valid_providers:
                raise ValidationError(
                    f"Invalid provider: {provider}. Must be one of {valid_providers}"
                )

            # Encrypt API key if provided
            api_key_secret_id = None
            if api_key:
                api_key_secret_id = encrypt_api_key(api_key)

            # If this is default, unset other defaults
            if is_default:
                await self._unset_all_defaults()

            # Create configuration
            config = ModelConfig(
                provider=provider,
                label=label,
                model_name=model_name,
                api_key_secret_id=api_key_secret_id,
                base_url=base_url,
                is_default=is_default,
                capabilities=capabilities
                or {
                    "streaming": True,
                    "vision": False,
                    "toolUse": True,
                    "multilingual": True,
                },
                guardrails=guardrails,
            )

            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)

            logger.info(f"Saved model configuration: {label} ({provider}/{model_name})")

            return config

        except ValidationError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to save model configuration: {str(e)}")
            raise ValidationError(f"Configuration save failed: {str(e)}")

    async def update_configuration(
        self, config_id: int, updates: Dict[str, Any]
    ) -> ModelConfig:
        """
        Update model configuration.

        Args:
            config_id: Configuration ID
            updates: Dictionary of updates

        Returns:
            Updated configuration

        Raises:
            ValidationError: If update fails
        """
        try:
            result = await self.db.execute(
                select(ModelConfig).where(ModelConfig.id == config_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                raise ValidationError(f"Configuration {config_id} not found")

            # Handle API key encryption
            if "api_key" in updates:
                api_key = updates.pop("api_key")
                if api_key:
                    updates["api_key_secret_id"] = encrypt_api_key(api_key)

            # Handle default flag
            if updates.get("is_default"):
                await self._unset_all_defaults()

            # Update fields
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            await self.db.commit()
            await self.db.refresh(config)

            logger.info(f"Updated model configuration: {config.label}")

            return config

        except ValidationError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update model configuration: {str(e)}")
            raise ValidationError(f"Configuration update failed: {str(e)}")

    async def delete_configuration(self, config_id: int) -> None:
        """
        Delete model configuration.

        Args:
            config_id: Configuration ID

        Raises:
            ValidationError: If deletion fails
        """
        try:
            result = await self.db.execute(
                select(ModelConfig).where(ModelConfig.id == config_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                raise ValidationError(f"Configuration {config_id} not found")

            if config.is_default:
                raise ValidationError("Cannot delete default configuration")

            await self.db.delete(config)
            await self.db.commit()

            logger.info(f"Deleted model configuration: {config.label}")

        except ValidationError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete model configuration: {str(e)}")
            raise ValidationError(f"Configuration deletion failed: {str(e)}")

    async def switch_model(
        self, config_id: Optional[int] = None, label: Optional[str] = None
    ) -> BaseChatModel:
        """
        Switch to a different model.

        Args:
            config_id: Optional configuration ID
            label: Optional configuration label

        Returns:
            New model instance

        Raises:
            ValidationError: If switching fails
        """
        try:
            # Load configuration
            if config_id:
                result = await self.db.execute(
                    select(ModelConfig).where(ModelConfig.id == config_id)
                )
                config = result.scalar_one_or_none()
            elif label:
                result = await self.db.execute(
                    select(ModelConfig).where(ModelConfig.label == label)
                )
                config = result.scalar_one_or_none()
            else:
                config = await self.get_default_configuration()

            if not config:
                raise ValidationError("Model configuration not found")

            # Create model instance
            model = await self._create_model_instance(config)

            self.current_model = model
            self.current_config = config

            logger.info(f"Switched to model: {config.label} ({config.provider}/{config.model_name})")

            return model

        except Exception as e:
            logger.error(f"Failed to switch model: {str(e)}")
            raise ValidationError(f"Model switch failed: {str(e)}")

    async def get_current_model(self) -> Optional[BaseChatModel]:
        """
        Get the currently active model.

        Returns:
            Current model instance or None
        """
        if not self.current_model:
            # Try to load default
            try:
                await self.switch_model()
            except Exception as e:
                logger.warning(f"Failed to load default model: {str(e)}")

        return self.current_model

    async def _create_model_instance(self, config: ModelConfig) -> BaseChatModel:
        """
        Create a model instance from configuration.

        Args:
            config: Model configuration

        Returns:
            Model instance

        Raises:
            ValidationError: If creation fails
        """
        try:
            # Decrypt API key if available
            api_key = None
            if config.api_key_secret_id:
                api_key = decrypt_api_key(config.api_key_secret_id)

            # Create model based on provider
            if config.provider == "anthropic":
                model = ChatAnthropic(
                    model=config.model_name,
                    anthropic_api_key=api_key or settings.ANTHROPIC_API_KEY,
                    base_url=config.base_url,
                    streaming=config.capabilities.get("streaming", True),
                )
            elif config.provider == "openai":
                model = ChatOpenAI(
                    model=config.model_name,
                    openai_api_key=api_key or settings.OPENAI_API_KEY,
                    base_url=config.base_url,
                    streaming=config.capabilities.get("streaming", True),
                )
            elif config.provider in ["doubao", "qianwen", "kimi", "local"]:
                # These providers use OpenAI-compatible API
                if not config.base_url:
                    raise ValidationError(f"base_url required for {config.provider}")

                model = ChatOpenAI(
                    model=config.model_name,
                    openai_api_key=api_key or "dummy-key",
                    base_url=config.base_url,
                    streaming=config.capabilities.get("streaming", True),
                )
            else:
                raise ValidationError(f"Unsupported provider: {config.provider}")

            return model

        except Exception as e:
            logger.error(f"Failed to create model instance: {str(e)}")
            raise ValidationError(f"Model creation failed: {str(e)}")

    async def _unset_all_defaults(self) -> None:
        """Unset is_default flag for all configurations."""
        result = await self.db.execute(
            select(ModelConfig).where(ModelConfig.is_default == True)
        )
        configs = result.scalars().all()

        for config in configs:
            config.is_default = False

        await self.db.flush()

    async def test_model_connection(self, config_id: int) -> Dict[str, Any]:
        """
        Test connection to a model.

        Args:
            config_id: Configuration ID

        Returns:
            Test results

        Raises:
            ValidationError: If test fails
        """
        try:
            result = await self.db.execute(
                select(ModelConfig).where(ModelConfig.id == config_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                raise ValidationError(f"Configuration {config_id} not found")

            # Create temporary model instance
            model = await self._create_model_instance(config)

            # Send simple test message
            import time

            start_time = time.time()
            response = await model.ainvoke("Hello")
            elapsed_time = time.time() - start_time

            return {
                "success": True,
                "provider": config.provider,
                "model": config.model_name,
                "response_time": elapsed_time,
                "response_preview": str(response.content)[:100] if hasattr(response, "content") else str(response)[:100],
            }

        except Exception as e:
            logger.error(f"Model connection test failed: {str(e)}")
            return {
                "success": False,
                "provider": config.provider if config else "unknown",
                "model": config.model_name if config else "unknown",
                "error": str(e),
            }
