"""Tests for the mcp-proxy module.

Tests are running in two modes:
- One where the server is exercised directly though an in memory client, just to
  set a baseline for the expected behavior.
- Another where the server is exercised through a proxy server, which forwards
  the requests to the original server.

The same test code is run on both to ensure parity.
"""

from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

import pytest
from mcp import types
from mcp.client.session import ClientSession
from mcp.server import Server
from mcp.shared.exceptions import McpError
from mcp.shared.memory import create_connected_server_and_client_session

from mcp_proxy import create_proxy_server

TOOL_INPUT_SCHEMA = {"type": "object", "properties": {"input1": {"type": "string"}}}

SessionContextManager = Callable[[Server], AbstractAsyncContextManager[ClientSession]]

# Direct server connection
in_memory: SessionContextManager = create_connected_server_and_client_session


@asynccontextmanager
async def proxy(server: Server) -> AsyncGenerator[ClientSession, None]:
    """Create a connection to the server through the proxy server."""
    async with in_memory(server) as session:
        wrapped_server = await create_proxy_server(session)
        async with in_memory(wrapped_server) as wrapped_session:
            yield wrapped_session


@pytest.fixture(params=["server", "proxy"])
def session_generator(request: pytest.FixtureRequest) -> SessionContextManager:
    """Fixture that returns a client creation strategy either direct or using the proxy."""
    if request.param == "server":
        return in_memory
    return proxy


async def test_list_prompts(session_generator: SessionContextManager) -> None:
    """Test list_prompts."""
    server = Server("prompt-server")

    @server.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        return [types.Prompt(name="prompt1")]

    async with session_generator(server) as session:
        result = await session.initialize()
        assert result.serverInfo.name == "prompt-server"
        assert result.capabilities
        assert result.capabilities.prompts
        assert not result.capabilities.tools
        assert not result.capabilities.resources
        assert not result.capabilities.logging

        list_prompts_result = await session.list_prompts()
        assert list_prompts_result.prompts == [types.Prompt(name="prompt1")]

        with pytest.raises(McpError, match="Method not found"):
            await session.list_tools()


async def test_list_tools(session_generator: SessionContextManager) -> None:
    """Test list_tools."""
    server = Server("tools-server")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="tool-name",
                description="tool-description",
                inputSchema=TOOL_INPUT_SCHEMA,
            ),
        ]

    async with session_generator(server) as session:
        result = await session.initialize()
        assert result.serverInfo.name == "tools-server"
        assert result.capabilities
        assert result.capabilities.tools
        assert not result.capabilities.prompts
        assert not result.capabilities.resources
        assert not result.capabilities.logging

        list_tools_result = await session.list_tools()
        assert len(list_tools_result.tools) == 1
        assert list_tools_result.tools[0].name == "tool-name"
        assert list_tools_result.tools[0].description == "tool-description"
        assert list_tools_result.tools[0].inputSchema == TOOL_INPUT_SCHEMA

        with pytest.raises(McpError, match="Method not found"):
            await session.list_prompts()
