"""
MCP Adapter Service

This module provides functionality to integrate Model Context Protocol (MCP) servers
with the writing assistant system. It handles server discovery, connection management,
tool conversion, and integration with LangChain.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool
from langchain_mcp import MCPToolkit
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.core.exceptions import MCPConnectionError, MCPToolConversionError

logger = logging.getLogger(__name__)


class MCPAdapter:
    """
    Adapter for integrating MCP servers with LangChain.

    This class provides methods to discover, connect to, and interact with MCP servers,
    as well as convert MCP tools to LangChain-compatible tools.

    Attributes:
        servers: Dictionary mapping server names to their configurations
        active_sessions: Dictionary mapping server names to active client sessions
        toolkits: Dictionary mapping server names to their MCPToolkit instances
    """

    def __init__(self) -> None:
        """Initialize the MCP adapter."""
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.active_sessions: Dict[str, ClientSession] = {}
        self.toolkits: Dict[str, MCPToolkit] = {}

    async def discover_servers(self, config_path: Optional[str] = None) -> List[str]:
        """
        Discover available MCP servers from configuration.

        Args:
            config_path: Optional path to MCP configuration file.
                        If not provided, uses default configuration.

        Returns:
            List of discovered server names

        Raises:
            MCPConnectionError: If discovery fails
        """
        try:
            # In a real implementation, this would read from a config file
            # For now, return empty list if no servers configured
            discovered = list(self.servers.keys())
            logger.info(f"Discovered {len(discovered)} MCP servers: {discovered}")
            return discovered
        except Exception as e:
            logger.error(f"Failed to discover MCP servers: {str(e)}")
            raise MCPConnectionError(f"Server discovery failed: {str(e)}")

    async def connect_server(
        self,
        server_name: str,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Connect to an MCP server.

        Args:
            server_name: Unique name for the server
            command: Command to start the MCP server
            args: Optional command arguments
            env: Optional environment variables

        Raises:
            MCPConnectionError: If connection fails
        """
        if server_name in self.active_sessions:
            logger.warning(f"Server {server_name} is already connected")
            return

        try:
            # Store server configuration
            self.servers[server_name] = {
                "command": command,
                "args": args or [],
                "env": env or {},
            }

            # Create server parameters
            server_params = StdioServerParameters(
                command=command,
                args=args or [],
                env=env,
            )

            # Create stdio client context
            stdio_transport = stdio_client(server_params)
            read, write = await stdio_transport.__aenter__()

            # Create and initialize session
            session = ClientSession(read, write)
            await session.__aenter__()
            await session.initialize()

            # Store active session
            self.active_sessions[server_name] = session

            # Create MCPToolkit for this server
            toolkit = MCPToolkit(session=session)
            self.toolkits[server_name] = toolkit

            logger.info(f"Successfully connected to MCP server: {server_name}")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_name}: {str(e)}")
            raise MCPConnectionError(f"Connection to {server_name} failed: {str(e)}")

    async def disconnect_server(self, server_name: str) -> None:
        """
        Disconnect from an MCP server.

        Args:
            server_name: Name of the server to disconnect

        Raises:
            MCPConnectionError: If disconnection fails
        """
        if server_name not in self.active_sessions:
            logger.warning(f"Server {server_name} is not connected")
            return

        try:
            session = self.active_sessions[server_name]
            await session.__aexit__(None, None, None)
            del self.active_sessions[server_name]

            if server_name in self.toolkits:
                del self.toolkits[server_name]

            logger.info(f"Successfully disconnected from MCP server: {server_name}")

        except Exception as e:
            logger.error(f"Failed to disconnect from MCP server {server_name}: {str(e)}")
            raise MCPConnectionError(f"Disconnection from {server_name} failed: {str(e)}")

    async def get_tools(self, server_name: Optional[str] = None) -> List[BaseTool]:
        """
        Get tools from connected MCP servers.

        Args:
            server_name: Optional server name. If provided, returns tools only from
                        that server. Otherwise, returns tools from all connected servers.

        Returns:
            List of LangChain-compatible tools

        Raises:
            MCPConnectionError: If server is not connected
            MCPToolConversionError: If tool conversion fails
        """
        try:
            tools: List[BaseTool] = []

            if server_name:
                # Get tools from specific server
                if server_name not in self.toolkits:
                    raise MCPConnectionError(f"Server {server_name} is not connected")

                toolkit = self.toolkits[server_name]
                server_tools = toolkit.get_tools()
                tools.extend(server_tools)
                logger.info(f"Retrieved {len(server_tools)} tools from {server_name}")

            else:
                # Get tools from all connected servers
                for name, toolkit in self.toolkits.items():
                    server_tools = toolkit.get_tools()
                    tools.extend(server_tools)
                    logger.info(f"Retrieved {len(server_tools)} tools from {name}")

            return tools

        except MCPConnectionError:
            raise
        except Exception as e:
            logger.error(f"Failed to get tools: {str(e)}")
            raise MCPToolConversionError(f"Tool retrieval failed: {str(e)}")

    async def convert_to_langchain_tool(
        self, mcp_tool: Any, server_name: str
    ) -> BaseTool:
        """
        Convert an MCP tool to a LangChain-compatible tool.

        Note: This method is primarily for internal use, as the MCPToolkit
        handles conversion automatically. It's provided for cases where
        manual conversion is needed.

        Args:
            mcp_tool: The MCP tool to convert
            server_name: Name of the server providing the tool

        Returns:
            LangChain-compatible tool

        Raises:
            MCPToolConversionError: If conversion fails
        """
        try:
            if server_name not in self.toolkits:
                raise MCPConnectionError(f"Server {server_name} is not connected")

            toolkit = self.toolkits[server_name]

            # MCPToolkit handles conversion internally
            # This method is provided for compatibility and custom conversion needs
            tools = toolkit.get_tools()

            # Find the matching tool
            for tool in tools:
                if hasattr(mcp_tool, "name") and tool.name == mcp_tool.name:
                    return tool

            raise MCPToolConversionError(
                f"Could not find converted tool for {getattr(mcp_tool, 'name', 'unknown')}"
            )

        except MCPConnectionError:
            raise
        except Exception as e:
            logger.error(f"Failed to convert MCP tool: {str(e)}")
            raise MCPToolConversionError(f"Tool conversion failed: {str(e)}")

    async def list_connected_servers(self) -> List[str]:
        """
        List all currently connected servers.

        Returns:
            List of connected server names
        """
        return list(self.active_sessions.keys())

    async def get_server_info(self, server_name: str) -> Dict[str, Any]:
        """
        Get information about a connected server.

        Args:
            server_name: Name of the server

        Returns:
            Dictionary containing server information

        Raises:
            MCPConnectionError: If server is not connected
        """
        if server_name not in self.servers:
            raise MCPConnectionError(f"Server {server_name} is not configured")

        if server_name not in self.active_sessions:
            raise MCPConnectionError(f"Server {server_name} is not connected")

        config = self.servers[server_name]
        toolkit = self.toolkits.get(server_name)
        tool_count = len(toolkit.get_tools()) if toolkit else 0

        return {
            "name": server_name,
            "command": config["command"],
            "args": config["args"],
            "connected": True,
            "tool_count": tool_count,
        }

    async def reconnect_server(self, server_name: str) -> None:
        """
        Reconnect to an MCP server.

        Args:
            server_name: Name of the server to reconnect

        Raises:
            MCPConnectionError: If reconnection fails
        """
        if server_name not in self.servers:
            raise MCPConnectionError(f"Server {server_name} is not configured")

        config = self.servers[server_name]

        # Disconnect if currently connected
        if server_name in self.active_sessions:
            await self.disconnect_server(server_name)

        # Reconnect
        await self.connect_server(
            server_name=server_name,
            command=config["command"],
            args=config["args"],
            env=config["env"],
        )

        logger.info(f"Successfully reconnected to MCP server: {server_name}")

    async def close_all(self) -> None:
        """
        Close all active MCP connections.

        This should be called when shutting down the application.
        """
        for server_name in list(self.active_sessions.keys()):
            try:
                await self.disconnect_server(server_name)
            except Exception as e:
                logger.error(f"Error disconnecting {server_name} during cleanup: {str(e)}")

        logger.info("All MCP connections closed")
