"""
MCP Configuration API Endpoints

This module provides API endpoints for managing MCP server configurations.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.config import MCPServerConfig
from app.models.user import User
from app.services.mcp_config_manager import MCPConfigManager

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class MCPServerConfigCreate(BaseModel):
    """Schema for creating MCP server configuration."""

    name: str = Field(..., description="Server name")
    protocol: str = Field(default="stdio", description="Protocol (stdio, http, ws)")
    command: Optional[str] = Field(None, description="Command for stdio protocol")
    args: Optional[List[str]] = Field(None, description="Command arguments")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    endpoint: Optional[str] = Field(None, description="Endpoint URL for http/ws")
    auth_type: str = Field(default="none", description="Authentication type")
    auth_secret_id: Optional[str] = Field(None, description="Auth secret ID")
    retry_policy: Dict[str, Any] = Field(
        default_factory=lambda: {"maxAttempts": 3, "backoffMs": 1000},
        description="Retry policy",
    )
    auto_reconnect: bool = Field(default=True, description="Auto-reconnect on startup")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "name": "example-mcp-server",
                "protocol": "stdio",
                "command": "npx",
                "args": ["-y", "@example/mcp-server"],
                "env": {"API_KEY": "secret"},
                "auto_reconnect": True,
            }
        }


class MCPServerConfigUpdate(BaseModel):
    """Schema for updating MCP server configuration."""

    name: Optional[str] = None
    protocol: Optional[str] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    endpoint: Optional[str] = None
    auth_type: Optional[str] = None
    auth_secret_id: Optional[str] = None
    retry_policy: Optional[Dict[str, Any]] = None
    auto_reconnect: Optional[bool] = None


class MCPServerConfigResponse(BaseModel):
    """Schema for MCP server configuration response."""

    id: int
    name: str
    protocol: str
    command: Optional[str]
    args: Optional[List[str]]
    endpoint: Optional[str]
    auth_type: str
    status: str
    last_connected_at: Optional[str]
    tool_count: int = 0
    retry_policy: Dict[str, Any]
    auto_reconnect: bool
    created_at: str
    updated_at: str

    class Config:
        """Pydantic config."""

        from_attributes = True


class MCPServerListResponse(BaseModel):
    """Schema for MCP server list response."""

    servers: List[MCPServerConfigResponse]
    total: int


class MCPServerActionRequest(BaseModel):
    """Schema for server action request."""

    action: str = Field(..., description="Action to perform (connect, disconnect, reconnect)")


class MCPConfigExportResponse(BaseModel):
    """Schema for configuration export response."""

    version: str
    servers: List[Dict[str, Any]]


class MCPConfigImportRequest(BaseModel):
    """Schema for configuration import request."""

    data: Dict[str, Any]
    overwrite: bool = Field(default=False, description="Overwrite existing configurations")


@router.get("/", response_model=MCPServerListResponse)
async def list_mcp_servers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MCPServerListResponse:
    """
    List all MCP server configurations.

    Returns:
        List of MCP server configurations
    """
    try:
        manager = MCPConfigManager(db)
        configs = await manager.load_configurations()

        # Get tool counts from adapter
        server_responses = []
        for config in configs:
            tool_count = 0
            if config.name in await manager.adapter.list_connected_servers():
                try:
                    tools = await manager.adapter.get_tools(config.name)
                    tool_count = len(tools)
                except Exception:
                    pass

            response = MCPServerConfigResponse(
                id=config.id,
                name=config.name,
                protocol=config.protocol,
                command=config.command,
                args=config.args,
                endpoint=config.endpoint,
                auth_type=config.auth_type,
                status=config.status,
                last_connected_at=str(config.last_connected_at) if config.last_connected_at else None,
                tool_count=tool_count,
                retry_policy=config.retry_policy,
                auto_reconnect=config.auto_reconnect,
                created_at=str(config.created_at),
                updated_at=str(config.updated_at),
            )
            server_responses.append(response)

        return MCPServerListResponse(servers=server_responses, total=len(server_responses))

    except Exception as e:
        logger.error(f"Failed to list MCP servers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list servers: {str(e)}",
        )


@router.post("/", response_model=MCPServerConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    config_data: MCPServerConfigCreate,
    connect: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MCPServerConfigResponse:
    """
    Create a new MCP server configuration.

    Args:
        config_data: Server configuration data
        connect: Whether to immediately connect to the server
        db: Database session
        current_user: Current user

    Returns:
        Created configuration
    """
    try:
        manager = MCPConfigManager(db)

        # Create configuration object
        config = MCPServerConfig(**config_data.model_dump())

        # Save configuration
        saved_config = await manager.save_configuration(config, connect=connect)

        # Get tool count if connected
        tool_count = 0
        if connect and saved_config.name in await manager.adapter.list_connected_servers():
            try:
                tools = await manager.adapter.get_tools(saved_config.name)
                tool_count = len(tools)
            except Exception:
                pass

        return MCPServerConfigResponse(
            id=saved_config.id,
            name=saved_config.name,
            protocol=saved_config.protocol,
            command=saved_config.command,
            args=saved_config.args,
            endpoint=saved_config.endpoint,
            auth_type=saved_config.auth_type,
            status=saved_config.status,
            last_connected_at=str(saved_config.last_connected_at) if saved_config.last_connected_at else None,
            tool_count=tool_count,
            retry_policy=saved_config.retry_policy,
            auto_reconnect=saved_config.auto_reconnect,
            created_at=str(saved_config.created_at),
            updated_at=str(saved_config.updated_at),
        )

    except Exception as e:
        logger.error(f"Failed to create MCP server: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create server: {str(e)}",
        )


@router.get("/{config_id}", response_model=MCPServerConfigResponse)
async def get_mcp_server(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MCPServerConfigResponse:
    """
    Get MCP server configuration by ID.

    Args:
        config_id: Configuration ID
        db: Database session
        current_user: Current user

    Returns:
        Server configuration
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(MCPServerConfig).where(MCPServerConfig.id == config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server {config_id} not found",
            )

        manager = MCPConfigManager(db)
        tool_count = 0
        if config.name in await manager.adapter.list_connected_servers():
            try:
                tools = await manager.adapter.get_tools(config.name)
                tool_count = len(tools)
            except Exception:
                pass

        return MCPServerConfigResponse(
            id=config.id,
            name=config.name,
            protocol=config.protocol,
            command=config.command,
            args=config.args,
            endpoint=config.endpoint,
            auth_type=config.auth_type,
            status=config.status,
            last_connected_at=str(config.last_connected_at) if config.last_connected_at else None,
            tool_count=tool_count,
            retry_policy=config.retry_policy,
            auto_reconnect=config.auto_reconnect,
            created_at=str(config.created_at),
            updated_at=str(config.updated_at),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MCP server: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server: {str(e)}",
        )


@router.patch("/{config_id}", response_model=MCPServerConfigResponse)
async def update_mcp_server(
    config_id: int,
    config_data: MCPServerConfigUpdate,
    reconnect: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MCPServerConfigResponse:
    """
    Update MCP server configuration.

    Args:
        config_id: Configuration ID
        config_data: Updated configuration data
        reconnect: Whether to reconnect after update
        db: Database session
        current_user: Current user

    Returns:
        Updated configuration
    """
    try:
        manager = MCPConfigManager(db)

        # Update configuration
        updates = {k: v for k, v in config_data.model_dump().items() if v is not None}
        updated_config = await manager.update_configuration(
            config_id, updates, reconnect=reconnect
        )

        # Get tool count
        tool_count = 0
        if updated_config.name in await manager.adapter.list_connected_servers():
            try:
                tools = await manager.adapter.get_tools(updated_config.name)
                tool_count = len(tools)
            except Exception:
                pass

        return MCPServerConfigResponse(
            id=updated_config.id,
            name=updated_config.name,
            protocol=updated_config.protocol,
            command=updated_config.command,
            args=updated_config.args,
            endpoint=updated_config.endpoint,
            auth_type=updated_config.auth_type,
            status=updated_config.status,
            last_connected_at=str(updated_config.last_connected_at) if updated_config.last_connected_at else None,
            tool_count=tool_count,
            retry_policy=updated_config.retry_policy,
            auto_reconnect=updated_config.auto_reconnect,
            created_at=str(updated_config.created_at),
            updated_at=str(updated_config.updated_at),
        )

    except Exception as e:
        logger.error(f"Failed to update MCP server: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update server: {str(e)}",
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(
    config_id: int,
    disconnect: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete MCP server configuration.

    Args:
        config_id: Configuration ID
        disconnect: Whether to disconnect before deletion
        db: Database session
        current_user: Current user
    """
    try:
        manager = MCPConfigManager(db)
        await manager.delete_configuration(config_id, disconnect=disconnect)

    except Exception as e:
        logger.error(f"Failed to delete MCP server: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete server: {str(e)}",
        )


@router.post("/{config_id}/action", response_model=MCPServerConfigResponse)
async def perform_server_action(
    config_id: int,
    action_request: MCPServerActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MCPServerConfigResponse:
    """
    Perform action on MCP server (connect, disconnect, reconnect).

    Args:
        config_id: Configuration ID
        action_request: Action to perform
        db: Database session
        current_user: Current user

    Returns:
        Updated configuration
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(MCPServerConfig).where(MCPServerConfig.id == config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server {config_id} not found",
            )

        manager = MCPConfigManager(db)

        if action_request.action == "connect":
            await manager.connect_server(config)
        elif action_request.action == "disconnect":
            await manager.disconnect_server(config)
        elif action_request.action == "reconnect":
            await manager.reconnect_server(config)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action_request.action}",
            )

        # Refresh configuration
        await db.refresh(config)

        # Get tool count
        tool_count = 0
        if config.name in await manager.adapter.list_connected_servers():
            try:
                tools = await manager.adapter.get_tools(config.name)
                tool_count = len(tools)
            except Exception:
                pass

        return MCPServerConfigResponse(
            id=config.id,
            name=config.name,
            protocol=config.protocol,
            command=config.command,
            args=config.args,
            endpoint=config.endpoint,
            auth_type=config.auth_type,
            status=config.status,
            last_connected_at=str(config.last_connected_at) if config.last_connected_at else None,
            tool_count=tool_count,
            retry_policy=config.retry_policy,
            auto_reconnect=config.auto_reconnect,
            created_at=str(config.created_at),
            updated_at=str(config.updated_at),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform server action: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform action: {str(e)}",
        )


@router.get("/export/all", response_model=MCPConfigExportResponse)
async def export_configurations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MCPConfigExportResponse:
    """
    Export all MCP configurations.

    Args:
        db: Database session
        current_user: Current user

    Returns:
        Exported configurations
    """
    try:
        manager = MCPConfigManager(db)
        exported_data = await manager.export_configurations()

        return MCPConfigExportResponse(**exported_data)

    except Exception as e:
        logger.error(f"Failed to export configurations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export: {str(e)}",
        )


@router.post("/import", response_model=MCPServerListResponse)
async def import_configurations(
    import_request: MCPConfigImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MCPServerListResponse:
    """
    Import MCP configurations.

    Args:
        import_request: Import request with configuration data
        db: Database session
        current_user: Current user

    Returns:
        Imported configurations
    """
    try:
        manager = MCPConfigManager(db)
        imported_configs = await manager.import_configurations(
            import_request.data, overwrite=import_request.overwrite
        )

        # Convert to response format
        server_responses = []
        for config in imported_configs:
            response = MCPServerConfigResponse(
                id=config.id,
                name=config.name,
                protocol=config.protocol,
                command=config.command,
                args=config.args,
                endpoint=config.endpoint,
                auth_type=config.auth_type,
                status=config.status,
                last_connected_at=str(config.last_connected_at) if config.last_connected_at else None,
                tool_count=0,
                retry_policy=config.retry_policy,
                auto_reconnect=config.auto_reconnect,
                created_at=str(config.created_at),
                updated_at=str(config.updated_at),
            )
            server_responses.append(response)

        return MCPServerListResponse(servers=server_responses, total=len(server_responses))

    except Exception as e:
        logger.error(f"Failed to import configurations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to import: {str(e)}",
        )
