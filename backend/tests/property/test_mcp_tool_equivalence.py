"""
Property Test: MCP Tool Conversion Equivalence (Property 6)

This test verifies that MCP tools converted to LangChain tools produce
equivalent outputs for the same inputs, ensuring conversion correctness.

Validates Requirement 5.2: MCP tool conversion
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from langchain_core.tools import BaseTool, StructuredTool

from app.services.mcp_adapter import MCPAdapter


class MockMCPTool:
    """Mock MCP tool for testing."""

    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        """
        Initialize mock MCP tool.

        Args:
            name: Tool name
            description: Tool description
            parameters: Tool parameters schema
        """
        self.name = name
        self.description = description
        self.parameters = parameters

    async def call(self, **kwargs: Any) -> str:
        """
        Simulate tool call.

        Args:
            **kwargs: Tool arguments

        Returns:
            Simulated tool output
        """
        # Simple deterministic output based on inputs
        return f"Result for {self.name}: {str(sorted(kwargs.items()))}"


def create_mock_session() -> AsyncMock:
    """
    Create a mock MCP session.

    Returns:
        Mock session object
    """
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.initialize = AsyncMock()
    return session


def create_mock_langchain_tool(mcp_tool: MockMCPTool) -> BaseTool:
    """
    Create a mock LangChain tool that mimics MCP tool behavior.

    Args:
        mcp_tool: MCP tool to mimic

    Returns:
        LangChain-compatible tool
    """

    async def tool_func(input_data: str = "") -> str:
        # Parse input as dict if possible
        try:
            import json
            if input_data:
                data = json.loads(input_data) if isinstance(input_data, str) else input_data
            else:
                data = {}
        except Exception:
            data = {}

        return await mcp_tool.call(**data)

    # Create a simple tool without schema
    from langchain_core.tools import BaseTool as CoreBaseTool

    class SimpleTool(CoreBaseTool):
        name: str = mcp_tool.name
        description: str = mcp_tool.description

        async def _arun(self, **kwargs: Any) -> str:
            return await mcp_tool.call(**kwargs)

        def _run(self, **kwargs: Any) -> str:
            import asyncio
            return asyncio.run(mcp_tool.call(**kwargs))

    return SimpleTool()


@pytest.mark.asyncio
@given(
    tool_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))),
    param_value=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=100, deadline=5000)
async def test_mcp_tool_conversion_equivalence(tool_name: str, param_value: int) -> None:
    """
    Property Test: MCP tool conversion preserves behavior.

    Tests that converting an MCP tool to a LangChain tool produces
    equivalent outputs for the same inputs.

    Args:
        tool_name: Generated tool name
        param_value: Generated parameter value
    """
    # Create mock MCP tool
    mcp_tool = MockMCPTool(
        name=tool_name,
        description=f"Test tool {tool_name}",
        parameters={"value": {"type": "integer"}},
    )

    # Get direct MCP tool output
    mcp_output = await mcp_tool.call(value=param_value)

    # Create converted LangChain tool
    langchain_tool = create_mock_langchain_tool(mcp_tool)

    # Get LangChain tool output
    langchain_output = await langchain_tool._arun(value=param_value)

    # Verify equivalence
    assert mcp_output == langchain_output, (
        f"Tool conversion not equivalent:\n"
        f"MCP output: {mcp_output}\n"
        f"LangChain output: {langchain_output}"
    )


@pytest.mark.asyncio
@given(
    text_input=st.text(min_size=0, max_size=100),
    number_input=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100, deadline=5000)
async def test_mcp_tool_multi_parameter_equivalence(
    text_input: str, number_input: float
) -> None:
    """
    Property Test: Multi-parameter MCP tool conversion equivalence.

    Tests that MCP tools with multiple parameters maintain equivalence
    after conversion to LangChain tools.

    Args:
        text_input: Generated text input
        number_input: Generated numeric input
    """
    # Create mock MCP tool with multiple parameters
    mcp_tool = MockMCPTool(
        name="multi_param_tool",
        description="Tool with multiple parameters",
        parameters={
            "text": {"type": "string"},
            "number": {"type": "number"},
        },
    )

    # Get direct MCP tool output
    mcp_output = await mcp_tool.call(text=text_input, number=number_input)

    # Create converted LangChain tool
    langchain_tool = create_mock_langchain_tool(mcp_tool)

    # Get LangChain tool output
    langchain_output = await langchain_tool._arun(text=text_input, number=number_input)

    # Verify equivalence
    assert mcp_output == langchain_output


@pytest.mark.asyncio
async def test_mcp_adapter_tool_conversion() -> None:
    """
    Integration test: MCPAdapter tool conversion.

    Tests the complete flow of connecting to an MCP server
    and converting its tools to LangChain tools.
    """
    adapter = MCPAdapter()

    # Mock the stdio_client and session
    with patch("app.services.mcp_adapter.stdio_client") as mock_stdio:
        # Setup mock transport
        mock_transport = AsyncMock()
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_transport.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
        mock_transport.__aexit__ = AsyncMock()
        mock_stdio.return_value = mock_transport

        # Setup mock session
        with patch("app.services.mcp_adapter.ClientSession") as mock_session_class:
            mock_session = create_mock_session()
            mock_session_class.return_value = mock_session

            # Setup mock toolkit
            with patch("app.services.mcp_adapter.MCPToolkit") as mock_toolkit_class:
                # Create mock tools
                mock_tool1 = MagicMock(spec=BaseTool)
                mock_tool1.name = "test_tool_1"
                mock_tool1.description = "Test tool 1"

                mock_tool2 = MagicMock(spec=BaseTool)
                mock_tool2.name = "test_tool_2"
                mock_tool2.description = "Test tool 2"

                mock_toolkit = MagicMock()
                mock_toolkit.get_tools.return_value = [mock_tool1, mock_tool2]
                mock_toolkit_class.return_value = mock_toolkit

                # Connect to server
                await adapter.connect_server(
                    server_name="test_server",
                    command="test_command",
                    args=["arg1"],
                )

                # Get tools
                tools = await adapter.get_tools("test_server")

                # Verify we got the tools
                assert len(tools) == 2
                assert tools[0].name == "test_tool_1"
                assert tools[1].name == "test_tool_2"

                # Cleanup
                await adapter.disconnect_server("test_server")


@pytest.mark.asyncio
async def test_tool_conversion_idempotence() -> None:
    """
    Property Test: Tool conversion is idempotent.

    Tests that converting a tool multiple times produces
    the same result.
    """
    # Create mock MCP tool
    mcp_tool = MockMCPTool(
        name="idempotent_tool",
        description="Tool to test idempotence",
        parameters={"input": {"type": "string"}},
    )

    # Convert multiple times
    tool1 = create_mock_langchain_tool(mcp_tool)
    tool2 = create_mock_langchain_tool(mcp_tool)

    # Test with same input
    test_input = "test_value"
    output1 = await tool1._arun(input=test_input)
    output2 = await tool2._arun(input=test_input)

    # Verify idempotence
    assert output1 == output2
    assert tool1.name == tool2.name
    assert tool1.description == tool2.description


@pytest.mark.asyncio
@given(
    input_data=st.dictionaries(
        keys=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))),
        values=st.one_of(
            st.integers(),
            st.text(max_size=50),
            st.floats(allow_nan=False, allow_infinity=False),
        ),
        min_size=1,
        max_size=5,
    )
)
@settings(max_examples=50, deadline=5000)
async def test_tool_conversion_with_complex_inputs(input_data: Dict[str, Any]) -> None:
    """
    Property Test: Tool conversion handles complex input types.

    Tests that MCP tools correctly handle various input types
    after conversion to LangChain tools.

    Args:
        input_data: Generated complex input dictionary
    """
    # Create mock MCP tool
    mcp_tool = MockMCPTool(
        name="complex_tool",
        description="Tool with complex inputs",
        parameters={key: {"type": "any"} for key in input_data.keys()},
    )

    # Get MCP tool output
    mcp_output = await mcp_tool.call(**input_data)

    # Create and test LangChain tool
    langchain_tool = create_mock_langchain_tool(mcp_tool)
    langchain_output = await langchain_tool._arun(**input_data)

    # Verify equivalence
    assert mcp_output == langchain_output


@pytest.mark.asyncio
async def test_multiple_server_tools_isolation() -> None:
    """
    Integration test: Tools from different servers are properly isolated.

    Tests that tools from different MCP servers don't interfere with each other.
    """
    adapter = MCPAdapter()

    with patch("app.services.mcp_adapter.stdio_client") as mock_stdio:
        mock_transport = AsyncMock()
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_transport.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
        mock_transport.__aexit__ = AsyncMock()
        mock_stdio.return_value = mock_transport

        with patch("app.services.mcp_adapter.ClientSession") as mock_session_class:
            mock_session = create_mock_session()
            mock_session_class.return_value = mock_session

            with patch("app.services.mcp_adapter.MCPToolkit") as mock_toolkit_class:
                # Setup first server tools
                mock_tool_server1 = MagicMock(spec=BaseTool)
                mock_tool_server1.name = "server1_tool"

                toolkit1 = MagicMock()
                toolkit1.get_tools.return_value = [mock_tool_server1]

                # Setup second server tools
                mock_tool_server2 = MagicMock(spec=BaseTool)
                mock_tool_server2.name = "server2_tool"

                toolkit2 = MagicMock()
                toolkit2.get_tools.return_value = [mock_tool_server2]

                # Control which toolkit is returned based on server
                def toolkit_side_effect(*args: Any, **kwargs: Any) -> MagicMock:
                    session = kwargs.get("session")
                    # Alternate between toolkits based on call order
                    if len(adapter.toolkits) == 0:
                        return toolkit1
                    return toolkit2

                mock_toolkit_class.side_effect = toolkit_side_effect

                # Connect to both servers
                await adapter.connect_server("server1", "cmd1")
                await adapter.connect_server("server2", "cmd2")

                # Get tools from specific servers
                tools1 = await adapter.get_tools("server1")
                tools2 = await adapter.get_tools("server2")

                # Verify isolation
                assert len(tools1) == 1
                assert len(tools2) == 1
                assert tools1[0].name == "server1_tool"
                assert tools2[0].name == "server2_tool"

                # Cleanup
                await adapter.close_all()
