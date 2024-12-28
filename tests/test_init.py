"""Tests for the mcp-proxy module."""

import pytest
import anyio
from mcp import types
from mcp.client.session import ClientSession
from mcp.server import Server
from mcp.shared.exceptions import McpError
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.server.stdio import stdio_server   

from mcp_proxy import configure_app, create_server

async def run_server() -> None:
    """Run a stdio server."""

    server = Server("test")

    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        return [
            types.Prompt(name="prompt1"),
        ]
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def test_list_prompts():
    """Test list_prompts."""

    client_to_server_send, client_to_server_receive = anyio.create_memory_object_stream[
        types.JSONRPCMessage
    ](1)
    server_to_client_send, server_to_client_receive = anyio.create_memory_object_stream[
        types.JSONRPCMessage
    ](1)

    server = Server("test")

    @server.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        return [
            types.Prompt(name="prompt1"),
        ]
    
    async def run_server() -> None:
        print("running server")
        await server.run(client_to_server_receive, server_to_client_send, server.create_initialization_options())

    async def listen_session():
        print("listening session")
        print(session)
        async for message in session.incoming_messages:
            if isinstance(message, Exception):
                raise message
            print("message")
            print(message)

    # Create an in memory connection to the fake server
    async with create_connected_server_and_client_session(server) as session:

        # Baseline behavior for client
        result = await session.list_prompts()
        assert result.prompts == [types.Prompt(name="prompt1")]

        with pytest.raises(McpError, match="Method not found"):
            await session.list_tools()

        # Create a proxy instance to the in memory server
        wrapped_server = await create_server("name", session)

        # Create a client to the proxy server
        async with create_connected_server_and_client_session(server) as wrapped_session:
            await wrapped_session.initialize()

            result = await wrapped_session.list_prompts()
            assert result.prompts == [types.Prompt(name="prompt1")]

            with pytest.raises(McpError, match="Method not found"):
                await wrapped_session.list_tools()
