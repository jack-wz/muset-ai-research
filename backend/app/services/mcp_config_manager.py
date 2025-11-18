"""
MCP Configuration Management Service

This module provides functionality to manage MCP server configurations,
including loading, saving, validation, and dynamic reconnection.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import MCPConnectionError, ValidationError
from app.models.config import MCPServerConfig
from app.services.mcp_adapter import MCPAdapter

logger = logging.getLogger(__name__)


class MCPConfigManager:
    """
    Manager for MCP server configurations.

    This class handles loading, saving, validation, and dynamic management
    of MCP server configurations.

    Attributes:
        db: Database session
        adapter: MCP adapter instance for managing connections
    """

    def __init__(self, db: AsyncSession, adapter: Optional[MCPAdapter] = None):
        """
        Initialize the MCP config manager.

        Args:
            db: Database session
            adapter: Optional MCP adapter instance
        """
        self.db = db
        self.adapter = adapter or MCPAdapter()

    async def load_configurations(
        self, workspace_id: Optional[int] = None
    ) -> List[MCPServerConfig]:
        """
        Load MCP server configurations from database.

        Args:
            workspace_id: Optional workspace ID to filter configurations

        Returns:
            List of MCP server configurations
        """
        try:
            query = select(MCPServerConfig)

            # TODO: Add workspace filtering when workspace relationship is implemented
            # if workspace_id:
            #     query = query.where(MCPServerConfig.workspace_id == workspace_id)

            result = await self.db.execute(query)
            configs = result.scalars().all()

            logger.info(f"Loaded {len(configs)} MCP configurations")
            return list(configs)

        except Exception as e:
            logger.error(f"Failed to load MCP configurations: {str(e)}")
            raise ValidationError(f"Configuration load failed: {str(e)}")

    async def save_configuration(
        self, config: MCPServerConfig, connect: bool = False
    ) -> MCPServerConfig:
        """
        Save MCP server configuration to database.

        Args:
            config: MCP server configuration
            connect: Whether to immediately connect to the server

        Returns:
            Saved configuration

        Raises:
            ValidationError: If configuration validation fails
            MCPConnectionError: If connection fails when connect=True
        """
        try:
            # Validate configuration
            await self.validate_configuration(config)

            # Save to database
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)

            logger.info(f"Saved MCP configuration: {config.name}")

            # Connect if requested
            if connect:
                await self.connect_server(config)

            return config

        except ValidationError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to save MCP configuration: {str(e)}")
            raise ValidationError(f"Configuration save failed: {str(e)}")

    async def update_configuration(
        self, config_id: int, updates: Dict[str, Any], reconnect: bool = False
    ) -> MCPServerConfig:
        """
        Update MCP server configuration.

        Args:
            config_id: Configuration ID
            updates: Dictionary of updates
            reconnect: Whether to reconnect after update

        Returns:
            Updated configuration

        Raises:
            ValidationError: If update validation fails
        """
        try:
            # Load existing configuration
            result = await self.db.execute(
                select(MCPServerConfig).where(MCPServerConfig.id == config_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                raise ValidationError(f"Configuration {config_id} not found")

            # Update fields
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            # Validate updated configuration
            await self.validate_configuration(config)

            # Save
            await self.db.commit()
            await self.db.refresh(config)

            logger.info(f"Updated MCP configuration: {config.name}")

            # Reconnect if requested
            if reconnect and config.name in await self.adapter.list_connected_servers():
                await self.adapter.reconnect_server(config.name)

            return config

        except ValidationError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update MCP configuration: {str(e)}")
            raise ValidationError(f"Configuration update failed: {str(e)}")

    async def delete_configuration(self, config_id: int, disconnect: bool = True) -> None:
        """
        Delete MCP server configuration.

        Args:
            config_id: Configuration ID
            disconnect: Whether to disconnect before deletion

        Raises:
            ValidationError: If deletion fails
        """
        try:
            # Load configuration
            result = await self.db.execute(
                select(MCPServerConfig).where(MCPServerConfig.id == config_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                raise ValidationError(f"Configuration {config_id} not found")

            # Disconnect if requested
            if disconnect and config.name in await self.adapter.list_connected_servers():
                await self.adapter.disconnect_server(config.name)

            # Delete from database
            await self.db.delete(config)
            await self.db.commit()

            logger.info(f"Deleted MCP configuration: {config.name}")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete MCP configuration: {str(e)}")
            raise ValidationError(f"Configuration deletion failed: {str(e)}")

    async def validate_configuration(self, config: MCPServerConfig) -> None:
        """
        Validate MCP server configuration.

        Args:
            config: Configuration to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate name
        if not config.name or not config.name.strip():
            raise ValidationError("Server name is required")

        # Validate protocol
        valid_protocols = ["stdio", "http", "ws"]
        if config.protocol not in valid_protocols:
            raise ValidationError(
                f"Invalid protocol: {config.protocol}. Must be one of {valid_protocols}"
            )

        # Protocol-specific validation
        if config.protocol == "stdio":
            if not config.command:
                raise ValidationError("Command is required for stdio protocol")
        elif config.protocol in ["http", "ws"]:
            if not config.endpoint:
                raise ValidationError(f"Endpoint is required for {config.protocol} protocol")

        # Validate retry policy
        if config.retry_policy:
            if "maxAttempts" in config.retry_policy:
                if not isinstance(config.retry_policy["maxAttempts"], int):
                    raise ValidationError("maxAttempts must be an integer")
                if config.retry_policy["maxAttempts"] < 1:
                    raise ValidationError("maxAttempts must be at least 1")

            if "backoffMs" in config.retry_policy:
                if not isinstance(config.retry_policy["backoffMs"], int):
                    raise ValidationError("backoffMs must be an integer")
                if config.retry_policy["backoffMs"] < 0:
                    raise ValidationError("backoffMs must be non-negative")

    async def connect_server(self, config: MCPServerConfig) -> None:
        """
        Connect to MCP server using configuration.

        Args:
            config: Server configuration

        Raises:
            MCPConnectionError: If connection fails
        """
        try:
            if config.protocol == "stdio":
                await self.adapter.connect_server(
                    server_name=config.name,
                    command=config.command,
                    args=config.args or [],
                    env=config.env or {},
                )
            else:
                # TODO: Implement HTTP/WS connection
                raise MCPConnectionError(
                    f"Protocol {config.protocol} not yet implemented for connections"
                )

            # Update status
            config.status = "connected"
            from datetime import datetime, timezone

            config.last_connected_at = datetime.now(timezone.utc)
            await self.db.commit()

            logger.info(f"Connected to MCP server: {config.name}")

        except MCPConnectionError:
            config.status = "error"
            await self.db.commit()
            raise
        except Exception as e:
            config.status = "error"
            await self.db.commit()
            logger.error(f"Failed to connect to MCP server {config.name}: {str(e)}")
            raise MCPConnectionError(f"Connection failed: {str(e)}")

    async def disconnect_server(self, config: MCPServerConfig) -> None:
        """
        Disconnect from MCP server.

        Args:
            config: Server configuration

        Raises:
            MCPConnectionError: If disconnection fails
        """
        try:
            await self.adapter.disconnect_server(config.name)

            # Update status
            config.status = "disconnected"
            await self.db.commit()

            logger.info(f"Disconnected from MCP server: {config.name}")

        except Exception as e:
            logger.error(f"Failed to disconnect from MCP server {config.name}: {str(e)}")
            raise MCPConnectionError(f"Disconnection failed: {str(e)}")

    async def reconnect_server(self, config: MCPServerConfig) -> None:
        """
        Reconnect to MCP server with dynamic reconnection.

        Args:
            config: Server configuration

        Raises:
            MCPConnectionError: If reconnection fails
        """
        try:
            # Disconnect if connected
            if config.name in await self.adapter.list_connected_servers():
                await self.disconnect_server(config)

            # Reconnect
            await self.connect_server(config)

            logger.info(f"Reconnected to MCP server: {config.name}")

        except Exception as e:
            logger.error(f"Failed to reconnect to MCP server {config.name}: {str(e)}")
            raise MCPConnectionError(f"Reconnection failed: {str(e)}")

    async def connect_all_auto_reconnect_servers(self) -> None:
        """
        Connect to all servers with auto_reconnect enabled.

        This should be called on application startup.
        """
        configs = await self.load_configurations()
        connected_count = 0

        for config in configs:
            if config.auto_reconnect:
                try:
                    await self.connect_server(config)
                    connected_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to auto-connect to {config.name} on startup: {str(e)}"
                    )

        logger.info(f"Auto-connected to {connected_count} MCP servers")

    async def export_configurations(
        self, config_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Export configurations to a dictionary.

        Args:
            config_ids: Optional list of config IDs to export. If None, exports all.

        Returns:
            Dictionary containing exported configurations
        """
        query = select(MCPServerConfig)
        if config_ids:
            query = query.where(MCPServerConfig.id.in_(config_ids))

        result = await self.db.execute(query)
        configs = result.scalars().all()

        exported = {
            "version": "1.0",
            "servers": [],
        }

        for config in configs:
            server_data = {
                "name": config.name,
                "protocol": config.protocol,
                "command": config.command,
                "args": config.args,
                "env": config.env,
                "endpoint": config.endpoint,
                "auth_type": config.auth_type,
                "retry_policy": config.retry_policy,
                "auto_reconnect": config.auto_reconnect,
            }
            exported["servers"].append(server_data)

        return exported

    async def import_configurations(
        self, data: Dict[str, Any], overwrite: bool = False
    ) -> List[MCPServerConfig]:
        """
        Import configurations from a dictionary.

        Args:
            data: Dictionary containing configurations to import
            overwrite: Whether to overwrite existing configurations

        Returns:
            List of imported configurations

        Raises:
            ValidationError: If import validation fails
        """
        if "servers" not in data:
            raise ValidationError("Invalid import data: missing 'servers' key")

        imported_configs = []

        for server_data in data["servers"]:
            try:
                # Check if server already exists
                result = await self.db.execute(
                    select(MCPServerConfig).where(MCPServerConfig.name == server_data["name"])
                )
                existing_config = result.scalar_one_or_none()

                if existing_config and not overwrite:
                    logger.warning(f"Skipping existing server: {server_data['name']}")
                    continue

                if existing_config and overwrite:
                    # Update existing
                    for key, value in server_data.items():
                        if hasattr(existing_config, key):
                            setattr(existing_config, key, value)
                    config = existing_config
                else:
                    # Create new
                    config = MCPServerConfig(**server_data)
                    self.db.add(config)

                await self.validate_configuration(config)
                imported_configs.append(config)

            except Exception as e:
                logger.error(f"Failed to import server {server_data.get('name')}: {str(e)}")
                continue

        await self.db.commit()
        logger.info(f"Imported {len(imported_configs)} MCP configurations")

        return imported_configs
