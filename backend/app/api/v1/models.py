"""
Model Configuration API Endpoints

This module provides API endpoints for managing AI model configurations.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.config import ModelConfig
from app.models.user import User
from app.services.model_config_manager import ModelConfigManager

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class ModelConfigCreate(BaseModel):
    """Schema for creating model configuration."""

    provider: str = Field(..., description="Provider (anthropic, openai, etc.)")
    label: str = Field(..., description="Human-readable label")
    model_name: str = Field(..., description="Model identifier")
    api_key: Optional[str] = Field(None, description="API key (will be encrypted)")
    base_url: Optional[str] = Field(None, description="Base URL for custom endpoints")
    is_default: bool = Field(default=False, description="Set as default model")
    capabilities: Optional[Dict[str, Any]] = Field(
        None, description="Model capabilities"
    )
    guardrails: Optional[Dict[str, Any]] = Field(None, description="Model guardrails")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "provider": "anthropic",
                "label": "Claude Sonnet",
                "model_name": "claude-3-5-sonnet-20241022",
                "api_key": "sk-ant-...",
                "is_default": True,
            }
        }


class ModelConfigUpdate(BaseModel):
    """Schema for updating model configuration."""

    provider: Optional[str] = None
    label: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_default: Optional[bool] = None
    capabilities: Optional[Dict[str, Any]] = None
    guardrails: Optional[Dict[str, Any]] = None


class ModelConfigResponse(BaseModel):
    """Schema for model configuration response."""

    id: int
    provider: str
    label: str
    model_name: str
    base_url: Optional[str]
    is_default: bool
    capabilities: Dict[str, Any]
    guardrails: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str

    class Config:
        """Pydantic config."""

        from_attributes = True


class ModelConfigListResponse(BaseModel):
    """Schema for model configuration list response."""

    models: List[ModelConfigResponse]
    total: int


class ModelTestResponse(BaseModel):
    """Schema for model test response."""

    success: bool
    provider: str
    model: str
    response_time: Optional[float] = None
    response_preview: Optional[str] = None
    error: Optional[str] = None


@router.get("/", response_model=ModelConfigListResponse)
async def list_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelConfigListResponse:
    """
    List all model configurations.

    Returns:
        List of model configurations
    """
    try:
        manager = ModelConfigManager(db)
        configs = await manager.load_configurations()

        model_responses = []
        for config in configs:
            response = ModelConfigResponse(
                id=config.id,
                provider=config.provider,
                label=config.label,
                model_name=config.model_name,
                base_url=config.base_url,
                is_default=config.is_default,
                capabilities=config.capabilities,
                guardrails=config.guardrails,
                created_at=str(config.created_at),
                updated_at=str(config.updated_at),
            )
            model_responses.append(response)

        return ModelConfigListResponse(models=model_responses, total=len(model_responses))

    except Exception as e:
        logger.error(f"Failed to list model configurations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}",
        )


@router.post("/", response_model=ModelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    config_data: ModelConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelConfigResponse:
    """
    Create a new model configuration.

    Args:
        config_data: Model configuration data
        db: Database session
        current_user: Current user

    Returns:
        Created configuration
    """
    try:
        manager = ModelConfigManager(db)

        config = await manager.save_configuration(
            provider=config_data.provider,
            label=config_data.label,
            model_name=config_data.model_name,
            api_key=config_data.api_key,
            base_url=config_data.base_url,
            is_default=config_data.is_default,
            capabilities=config_data.capabilities,
            guardrails=config_data.guardrails,
        )

        return ModelConfigResponse(
            id=config.id,
            provider=config.provider,
            label=config.label,
            model_name=config.model_name,
            base_url=config.base_url,
            is_default=config.is_default,
            capabilities=config.capabilities,
            guardrails=config.guardrails,
            created_at=str(config.created_at),
            updated_at=str(config.updated_at),
        )

    except Exception as e:
        logger.error(f"Failed to create model configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create model: {str(e)}",
        )


@router.get("/{config_id}", response_model=ModelConfigResponse)
async def get_model(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelConfigResponse:
    """
    Get model configuration by ID.

    Args:
        config_id: Configuration ID
        db: Database session
        current_user: Current user

    Returns:
        Model configuration
    """
    try:
        result = await db.execute(
            select(ModelConfig).where(ModelConfig.id == config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {config_id} not found",
            )

        return ModelConfigResponse(
            id=config.id,
            provider=config.provider,
            label=config.label,
            model_name=config.model_name,
            base_url=config.base_url,
            is_default=config.is_default,
            capabilities=config.capabilities,
            guardrails=config.guardrails,
            created_at=str(config.created_at),
            updated_at=str(config.updated_at),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model: {str(e)}",
        )


@router.patch("/{config_id}", response_model=ModelConfigResponse)
async def update_model(
    config_id: int,
    config_data: ModelConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelConfigResponse:
    """
    Update model configuration.

    Args:
        config_id: Configuration ID
        config_data: Updated configuration data
        db: Database session
        current_user: Current user

    Returns:
        Updated configuration
    """
    try:
        manager = ModelConfigManager(db)

        # Update configuration
        updates = {k: v for k, v in config_data.model_dump().items() if v is not None}
        updated_config = await manager.update_configuration(config_id, updates)

        return ModelConfigResponse(
            id=updated_config.id,
            provider=updated_config.provider,
            label=updated_config.label,
            model_name=updated_config.model_name,
            base_url=updated_config.base_url,
            is_default=updated_config.is_default,
            capabilities=updated_config.capabilities,
            guardrails=updated_config.guardrails,
            created_at=str(updated_config.created_at),
            updated_at=str(updated_config.updated_at),
        )

    except Exception as e:
        logger.error(f"Failed to update model configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update model: {str(e)}",
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete model configuration.

    Args:
        config_id: Configuration ID
        db: Database session
        current_user: Current user
    """
    try:
        manager = ModelConfigManager(db)
        await manager.delete_configuration(config_id)

    except Exception as e:
        logger.error(f"Failed to delete model configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete model: {str(e)}",
        )


@router.post("/{config_id}/test", response_model=ModelTestResponse)
async def test_model(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelTestResponse:
    """
    Test model connection.

    Args:
        config_id: Configuration ID
        db: Database session
        current_user: Current user

    Returns:
        Test results
    """
    try:
        manager = ModelConfigManager(db)
        result = await manager.test_model_connection(config_id)

        return ModelTestResponse(**result)

    except Exception as e:
        logger.error(f"Failed to test model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test model: {str(e)}",
        )


@router.post("/{config_id}/set-default", response_model=ModelConfigResponse)
async def set_default_model(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelConfigResponse:
    """
    Set model as default.

    Args:
        config_id: Configuration ID
        db: Database session
        current_user: Current user

    Returns:
        Updated configuration
    """
    try:
        manager = ModelConfigManager(db)
        updated_config = await manager.update_configuration(
            config_id, {"is_default": True}
        )

        return ModelConfigResponse(
            id=updated_config.id,
            provider=updated_config.provider,
            label=updated_config.label,
            model_name=updated_config.model_name,
            base_url=updated_config.base_url,
            is_default=updated_config.is_default,
            capabilities=updated_config.capabilities,
            guardrails=updated_config.guardrails,
            created_at=str(updated_config.created_at),
            updated_at=str(updated_config.updated_at),
        )

    except Exception as e:
        logger.error(f"Failed to set default model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to set default model: {str(e)}",
        )


class ModelConfigExportResponse(BaseModel):
    """Schema for model configuration export response."""

    version: str
    models: List[Dict[str, Any]]


class ModelConfigImportRequest(BaseModel):
    """Schema for model configuration import request."""

    data: Dict[str, Any]
    overwrite: bool = Field(default=False, description="Overwrite existing configurations")


@router.get("/export/all", response_model=ModelConfigExportResponse)
async def export_configurations(
    include_api_keys: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelConfigExportResponse:
    """
    Export all model configurations.

    Args:
        include_api_keys: Whether to include API keys (default: False for security)
        db: Database session
        current_user: Current user

    Returns:
        Exported configurations

    Warning:
        API keys are excluded by default. If include_api_keys=True, ensure
        the export is handled securely and not shared publicly.
    """
    try:
        manager = ModelConfigManager(db)
        exported_data = await manager.export_configurations(
            include_api_keys=include_api_keys
        )

        return ModelConfigExportResponse(**exported_data)

    except Exception as e:
        logger.error(f"Failed to export configurations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export: {str(e)}",
        )


@router.post("/import", response_model=ModelConfigListResponse)
async def import_configurations(
    import_request: ModelConfigImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelConfigListResponse:
    """
    Import model configurations.

    Args:
        import_request: Import request with configuration data
        db: Database session
        current_user: Current user

    Returns:
        Imported configurations

    Note:
        Configurations with the same label will be skipped unless
        overwrite=True in the request.
    """
    try:
        manager = ModelConfigManager(db)
        imported_configs = await manager.import_configurations(
            import_request.data, overwrite=import_request.overwrite
        )

        # Convert to response format
        model_responses = []
        for config in imported_configs:
            response = ModelConfigResponse(
                id=config.id,
                provider=config.provider,
                label=config.label,
                model_name=config.model_name,
                base_url=config.base_url,
                is_default=config.is_default,
                capabilities=config.capabilities,
                guardrails=config.guardrails,
                created_at=str(config.created_at),
                updated_at=str(config.updated_at),
            )
            model_responses.append(response)

        return ModelConfigListResponse(models=model_responses, total=len(model_responses))

    except Exception as e:
        logger.error(f"Failed to import configurations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to import: {str(e)}",
        )
