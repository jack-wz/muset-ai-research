"""
Unit Tests for MCP Adapter

Tests server discovery, connection management, tool conversion, and error handling.
Validates Requirements 5.1-5.3
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.tools import BaseTool

from app.core.exceptions import MCPConnectionError, MCPToolConversionError
from app.services.mcp_adapter import MCPAdapter


@pytest.fixture
def adapter() -> MCPAdapter:
    """Create MCP adapter instance for testing."""
    return MCPAdapter()


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create mock MCP session."""
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.initialize = AsyncMock()
    return session


@pytest.fixture
def mock_toolkit() -> MagicMock:
    """Create mock MCP toolkit."""
    toolkit = MagicMock()
    tool1 = MagicMock(spec=BaseTool)
    tool1.name = "test_tool_1"
    tool1.description = "Test tool 1"

    tool2 = MagicMock(spec=BaseTool)
    tool2.name = "test_tool_2"
    tool2.description = "Test tool 2"

    toolkit.get_tools.return_value = [tool1, tool2]
    return toolkit


class TestServerDiscovery:
    """Tests for MCP server discovery."""

    @pytest.mark.asyncio
    async def test_discover_servers_empty(self, adapter: MCPAdapter) -> None:
        """Test discovering servers when none are configured."""
        servers = await adapter.discover_servers()
        assert servers == []
        assert isinstance(servers, list)

    @pytest.mark.asyncio
    async def test_discover_servers_with_configured(self, adapter: MCPAdapter) -> None:
        """Test discovering servers that are configured."""
        # Configure some servers
        adapter.servers = {
            "server1": {"command": "cmd1"},
            "server2": {"command": "cmd2"},
        }

        servers = await adapter.discover_servers()
        assert len(servers) == 2
        assert "server1" in servers
        assert "server2" in servers

    @pytest.mark.asyncio
    async def test_discover_servers_error_handling(self, adapter: MCPAdapter) -> None:
        """Test error handling during server discovery."""
        # This test is actually testing if we can handle errors during discovery
        # Since discover_servers doesn't currently have a way to fail,
        # we just verify it doesn't raise for now
        servers = await adapter.discover_servers()
        assert isinstance(servers, list)


class TestServerConnection:
    """Tests for MCP server connection management."""

    @pytest.mark.asyncio
    async def test_connect_server_success(
        self, adapter: MCPAdapter, mock_session: AsyncMock, mock_toolkit: MagicMock
    ) -> None:
        """Test successful server connection."""
        with patch("app.services.mcp_adapter.stdio_client") as mock_stdio:
            # Setup mock transport
            mock_transport = AsyncMock()
            mock_read = AsyncMock()
            mock_write = AsyncMock()
            mock_transport.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
            mock_transport.__aexit__ = AsyncMock()
            mock_stdio.return_value = mock_transport

            with patch("app.services.mcp_adapter.ClientSession", return_value=mock_session):
                with patch("app.services.mcp_adapter.MCPToolkit", return_value=mock_toolkit):
                    await adapter.connect_server(
                        server_name="test_server",
                        command="test_command",
                        args=["arg1", "arg2"],
                        env={"KEY": "value"},
                    )

                    # Verify server is connected
                    assert "test_server" in adapter.active_sessions
                    assert "test_server" in adapter.servers
                    assert "test_server" in adapter.toolkits

                    # Verify server configuration
                    config = adapter.servers["test_server"]
                    assert config["command"] == "test_command"
                    assert config["args"] == ["arg1", "arg2"]
                    assert config["env"] == {"KEY": "value"}

    @pytest.mark.asyncio
    async def test_connect_already_connected_server(
        self, adapter: MCPAdapter, mock_session: AsyncMock
    ) -> None:
        """Test connecting to an already connected server."""
        adapter.active_sessions["test_server"] = mock_session

        # Should not raise error, just log warning
        with patch("app.services.mcp_adapter.stdio_client"):
            await adapter.connect_server("test_server", "test_command")

    @pytest.mark.asyncio
    async def test_connect_server_failure(self, adapter: MCPAdapter) -> None:
        """Test server connection failure."""
        with patch(
            "app.services.mcp_adapter.stdio_client", side_effect=Exception("Connection failed")
        ):
            with pytest.raises(MCPConnectionError, match="Connection to test_server failed"):
                await adapter.connect_server("test_server", "test_command")

    @pytest.mark.asyncio
    async def test_disconnect_server_success(
        self, adapter: MCPAdapter, mock_session: AsyncMock
    ) -> None:
        """Test successful server disconnection."""
        adapter.active_sessions["test_server"] = mock_session
        adapter.toolkits["test_server"] = MagicMock()

        await adapter.disconnect_server("test_server")

        assert "test_server" not in adapter.active_sessions
        assert "test_server" not in adapter.toolkits
        mock_session.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_not_connected_server(self, adapter: MCPAdapter) -> None:
        """Test disconnecting a server that is not connected."""
        # Should not raise error, just log warning
        await adapter.disconnect_server("nonexistent_server")

    @pytest.mark.asyncio
    async def test_disconnect_server_failure(
        self, adapter: MCPAdapter, mock_session: AsyncMock
    ) -> None:
        """Test server disconnection failure."""
        mock_session.__aexit__.side_effect = Exception("Disconnection failed")
        adapter.active_sessions["test_server"] = mock_session

        with pytest.raises(MCPConnectionError, match="Disconnection from test_server failed"):
            await adapter.disconnect_server("test_server")


class TestToolRetrieval:
    """Tests for tool retrieval and conversion."""

    @pytest.mark.asyncio
    async def test_get_tools_from_specific_server(
        self, adapter: MCPAdapter, mock_toolkit: MagicMock
    ) -> None:
        """Test getting tools from a specific server."""
        adapter.toolkits["test_server"] = mock_toolkit

        tools = await adapter.get_tools("test_server")

        assert len(tools) == 2
        assert tools[0].name == "test_tool_1"
        assert tools[1].name == "test_tool_2"
        mock_toolkit.get_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tools_from_all_servers(self, adapter: MCPAdapter) -> None:
        """Test getting tools from all connected servers."""
        # Setup multiple servers with tools
        toolkit1 = MagicMock()
        tool1 = MagicMock(spec=BaseTool)
        tool1.name = "server1_tool"
        toolkit1.get_tools.return_value = [tool1]

        toolkit2 = MagicMock()
        tool2 = MagicMock(spec=BaseTool)
        tool2.name = "server2_tool"
        toolkit2.get_tools.return_value = [tool2]

        adapter.toolkits["server1"] = toolkit1
        adapter.toolkits["server2"] = toolkit2

        tools = await adapter.get_tools()

        assert len(tools) == 2
        assert any(t.name == "server1_tool" for t in tools)
        assert any(t.name == "server2_tool" for t in tools)

    @pytest.mark.asyncio
    async def test_get_tools_from_not_connected_server(self, adapter: MCPAdapter) -> None:
        """Test getting tools from a server that is not connected."""
        with pytest.raises(MCPConnectionError, match="Server test_server is not connected"):
            await adapter.get_tools("test_server")

    @pytest.mark.asyncio
    async def test_get_tools_conversion_error(self, adapter: MCPAdapter) -> None:
        """Test tool conversion error handling."""
        toolkit = MagicMock()
        toolkit.get_tools.side_effect = Exception("Conversion failed")
        adapter.toolkits["test_server"] = toolkit

        with pytest.raises(MCPToolConversionError, match="Tool retrieval failed"):
            await adapter.get_tools("test_server")

    @pytest.mark.asyncio
    async def test_convert_to_langchain_tool(
        self, adapter: MCPAdapter, mock_toolkit: MagicMock
    ) -> None:
        """Test converting an MCP tool to LangChain tool."""
        adapter.toolkits["test_server"] = mock_toolkit

        # Create mock MCP tool
        mcp_tool = MagicMock()
        mcp_tool.name = "test_tool_1"

        tool = await adapter.convert_to_langchain_tool(mcp_tool, "test_server")

        assert tool.name == "test_tool_1"

    @pytest.mark.asyncio
    async def test_convert_tool_server_not_connected(self, adapter: MCPAdapter) -> None:
        """Test tool conversion when server is not connected."""
        mcp_tool = MagicMock()
        mcp_tool.name = "test_tool"

        with pytest.raises(MCPConnectionError, match="Server test_server is not connected"):
            await adapter.convert_to_langchain_tool(mcp_tool, "test_server")

    @pytest.mark.asyncio
    async def test_convert_tool_not_found(
        self, adapter: MCPAdapter, mock_toolkit: MagicMock
    ) -> None:
        """Test tool conversion when tool is not found."""
        adapter.toolkits["test_server"] = mock_toolkit

        mcp_tool = MagicMock()
        mcp_tool.name = "nonexistent_tool"

        with pytest.raises(MCPToolConversionError, match="Could not find converted tool"):
            await adapter.convert_to_langchain_tool(mcp_tool, "test_server")


class TestServerManagement:
    """Tests for server management operations."""

    @pytest.mark.asyncio
    async def test_list_connected_servers(self, adapter: MCPAdapter) -> None:
        """Test listing connected servers."""
        adapter.active_sessions["server1"] = AsyncMock()
        adapter.active_sessions["server2"] = AsyncMock()

        servers = await adapter.list_connected_servers()

        assert len(servers) == 2
        assert "server1" in servers
        assert "server2" in servers

    @pytest.mark.asyncio
    async def test_get_server_info_success(
        self, adapter: MCPAdapter, mock_session: AsyncMock, mock_toolkit: MagicMock
    ) -> None:
        """Test getting server information."""
        adapter.servers["test_server"] = {
            "command": "test_command",
            "args": ["arg1"],
            "env": {"KEY": "value"},
        }
        adapter.active_sessions["test_server"] = mock_session
        adapter.toolkits["test_server"] = mock_toolkit

        info = await adapter.get_server_info("test_server")

        assert info["name"] == "test_server"
        assert info["command"] == "test_command"
        assert info["args"] == ["arg1"]
        assert info["connected"] is True
        assert info["tool_count"] == 2

    @pytest.mark.asyncio
    async def test_get_server_info_not_configured(self, adapter: MCPAdapter) -> None:
        """Test getting info for a server that is not configured."""
        with pytest.raises(MCPConnectionError, match="Server test_server is not configured"):
            await adapter.get_server_info("test_server")

    @pytest.mark.asyncio
    async def test_get_server_info_not_connected(self, adapter: MCPAdapter) -> None:
        """Test getting info for a configured but not connected server."""
        adapter.servers["test_server"] = {"command": "test_command"}

        with pytest.raises(MCPConnectionError, match="Server test_server is not connected"):
            await adapter.get_server_info("test_server")

    @pytest.mark.asyncio
    async def test_reconnect_server_success(
        self, adapter: MCPAdapter, mock_session: AsyncMock, mock_toolkit: MagicMock
    ) -> None:
        """Test reconnecting to a server."""
        adapter.servers["test_server"] = {
            "command": "test_command",
            "args": ["arg1"],
            "env": {"KEY": "value"},
        }
        adapter.active_sessions["test_server"] = mock_session

        with patch("app.services.mcp_adapter.stdio_client") as mock_stdio:
            mock_transport = AsyncMock()
            mock_read = AsyncMock()
            mock_write = AsyncMock()
            mock_transport.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
            mock_transport.__aexit__ = AsyncMock()
            mock_stdio.return_value = mock_transport

            new_session = AsyncMock()
            new_session.__aenter__ = AsyncMock(return_value=new_session)
            new_session.__aexit__ = AsyncMock(return_value=None)
            new_session.initialize = AsyncMock()

            with patch("app.services.mcp_adapter.ClientSession", return_value=new_session):
                with patch("app.services.mcp_adapter.MCPToolkit", return_value=mock_toolkit):
                    await adapter.reconnect_server("test_server")

                    # Verify old session was closed
                    mock_session.__aexit__.assert_called_once()

                    # Verify new session is active
                    assert adapter.active_sessions["test_server"] == new_session

    @pytest.mark.asyncio
    async def test_reconnect_server_not_configured(self, adapter: MCPAdapter) -> None:
        """Test reconnecting to a server that is not configured."""
        with pytest.raises(MCPConnectionError, match="Server test_server is not configured"):
            await adapter.reconnect_server("test_server")

    @pytest.mark.asyncio
    async def test_close_all_connections(self, adapter: MCPAdapter) -> None:
        """Test closing all connections."""
        session1 = AsyncMock()
        session1.__aexit__ = AsyncMock()
        session2 = AsyncMock()
        session2.__aexit__ = AsyncMock()

        adapter.active_sessions["server1"] = session1
        adapter.active_sessions["server2"] = session2
        adapter.toolkits["server1"] = MagicMock()
        adapter.toolkits["server2"] = MagicMock()

        await adapter.close_all()

        assert len(adapter.active_sessions) == 0
        assert len(adapter.toolkits) == 0
        session1.__aexit__.assert_called_once()
        session2.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_all_with_errors(self, adapter: MCPAdapter) -> None:
        """Test closing all connections when some fail."""
        session1 = AsyncMock()
        session1.__aexit__ = AsyncMock(side_effect=Exception("Disconnect error"))
        session2 = AsyncMock()
        session2.__aexit__ = AsyncMock()

        adapter.active_sessions["server1"] = session1
        adapter.active_sessions["server2"] = session2

        # Should not raise error, just log
        await adapter.close_all()

        # Both sessions should have been attempted to close
        session1.__aexit__.assert_called_once()
        session2.__aexit__.assert_called_once()
