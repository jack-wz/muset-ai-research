"""
Unified Configuration Import/Export API

This module provides endpoints for importing and exporting all system configurations
(models, MCP servers, and skills) in a unified format.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.mcp_config_manager import MCPConfigManager
from app.services.model_config_manager import ModelConfigManager

logger = logging.getLogger(__name__)

router = APIRouter()


class UnifiedConfigExportResponse(BaseModel):
    """Schema for unified configuration export response."""

    version: str
    models: Dict[str, Any]
    mcp_servers: Dict[str, Any]
    # skills: Dict[str, Any]  # Can be added later


class UnifiedConfigImportRequest(BaseModel):
    """Schema for unified configuration import request."""

    data: Dict[str, Any]
    overwrite: bool = Field(
        default=False, description="Overwrite existing configurations"
    )


@router.get("/export", response_model=UnifiedConfigExportResponse)
async def export_all_configurations(
    include_api_keys: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UnifiedConfigExportResponse:
    """
    Export all system configurations (models, MCP servers, skills).

    Args:
        include_api_keys: Whether to include API keys (default: False for security)
        db: Database session
        current_user: Current user

    Returns:
        All configurations in unified format

    Warning:
        API keys and sensitive information are excluded by default.
        Set include_api_keys=True only for secure backup purposes.
    """
    try:
        # Export model configurations
        model_manager = ModelConfigManager(db)
        models_data = await model_manager.export_configurations(
            include_api_keys=include_api_keys
        )

        # Export MCP configurations
        mcp_manager = MCPConfigManager(db)
        mcp_data = await mcp_manager.export_configurations()

        # Combine all configurations
        unified_export = {
            "version": "1.0",
            "models": models_data,
            "mcp_servers": mcp_data,
        }

        logger.info(
            f"Exported unified configuration with {len(models_data.get('models', []))} models "
            f"and {len(mcp_data.get('servers', []))} MCP servers"
        )

        return UnifiedConfigExportResponse(**unified_export)

    except Exception as e:
        logger.error(f"Failed to export configurations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export configurations: {str(e)}",
        )


@router.post("/import")
async def import_all_configurations(
    import_request: UnifiedConfigImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Import all system configurations (models, MCP servers, skills).

    Args:
        import_request: Import request with unified configuration data
        db: Database session
        current_user: Current user

    Returns:
        Summary of imported configurations

    Note:
        Configurations with existing names/labels will be skipped unless
        overwrite=True in the request.
    """
    try:
        results = {
            "models_imported": 0,
            "mcp_servers_imported": 0,
            "errors": [],
        }

        data = import_request.data
        overwrite = import_request.overwrite

        # Import model configurations
        if "models" in data:
            try:
                model_manager = ModelConfigManager(db)
                imported_models = await model_manager.import_configurations(
                    data["models"], overwrite=overwrite
                )
                results["models_imported"] = len(imported_models)
                logger.info(f"Imported {len(imported_models)} model configurations")
            except Exception as e:
                error_msg = f"Failed to import models: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

        # Import MCP configurations
        if "mcp_servers" in data:
            try:
                mcp_manager = MCPConfigManager(db)
                imported_servers = await mcp_manager.import_configurations(
                    data["mcp_servers"], overwrite=overwrite
                )
                results["mcp_servers_imported"] = len(imported_servers)
                logger.info(f"Imported {len(imported_servers)} MCP server configurations")
            except Exception as e:
                error_msg = f"Failed to import MCP servers: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

        # Return summary
        if results["errors"] and results["models_imported"] == 0 and results["mcp_servers_imported"] == 0:
            # Complete failure
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Import failed: {'; '.join(results['errors'])}",
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import configurations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import configurations: {str(e)}",
        )


@router.post("/validate")
async def validate_configuration(
    config_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Validate configuration data before import.

    Args:
        config_data: Configuration data to validate
        current_user: Current user

    Returns:
        Validation results

    Note:
        This endpoint validates the structure and content of configuration
        data without actually importing it. Useful for previewing imports.
    """
    try:
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "preview": {
                "models_count": 0,
                "mcp_servers_count": 0,
            },
        }

        # Validate version
        if "version" not in config_data:
            validation_results["warnings"].append("Missing version field")
        elif config_data["version"] != "1.0":
            validation_results["warnings"].append(
                f"Unsupported version: {config_data['version']}"
            )

        # Validate models
        if "models" in config_data:
            models_data = config_data["models"]
            if "models" in models_data and isinstance(models_data["models"], list):
                validation_results["preview"]["models_count"] = len(models_data["models"])

                # Check required fields
                for idx, model in enumerate(models_data["models"]):
                    required_fields = ["provider", "label", "model_name"]
                    missing_fields = [f for f in required_fields if f not in model]
                    if missing_fields:
                        validation_results["errors"].append(
                            f"Model #{idx + 1} missing required fields: {missing_fields}"
                        )
                        validation_results["valid"] = False
            else:
                validation_results["errors"].append("Invalid models data structure")
                validation_results["valid"] = False

        # Validate MCP servers
        if "mcp_servers" in config_data:
            mcp_data = config_data["mcp_servers"]
            if "servers" in mcp_data and isinstance(mcp_data["servers"], list):
                validation_results["preview"]["mcp_servers_count"] = len(
                    mcp_data["servers"]
                )

                # Check required fields
                for idx, server in enumerate(mcp_data["servers"]):
                    if "name" not in server:
                        validation_results["errors"].append(
                            f"MCP server #{idx + 1} missing required field: name"
                        )
                        validation_results["valid"] = False
            else:
                validation_results["errors"].append("Invalid MCP servers data structure")
                validation_results["valid"] = False

        return validation_results

    except Exception as e:
        logger.error(f"Failed to validate configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed: {str(e)}",
        )
