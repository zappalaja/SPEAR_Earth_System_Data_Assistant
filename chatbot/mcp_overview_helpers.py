"""
mcp_overview_helpers.py — API client functions for the MCP Tools Overview page.

Supports two modes controlled by MCP_TOOLS_VIA_SSE env var (default: true):
  - SSE mode: connects via MCP SSE protocol (works with standard MCP servers)
  - REST mode: calls /tools REST endpoint (requires server to expose that route)
"""

import asyncio
import os
import requests
from typing import Any, Dict, List

# Set MCP_TOOLS_VIA_SSE=false in .env to revert to the original REST approach
_USE_SSE = os.getenv("MCP_TOOLS_VIA_SSE", "true").lower() == "true"


def _mcp_url() -> str:
    return os.getenv("MCP_SERVER_URL", "http://localhost:8000").rstrip("/")


# ── SSE approach (default) ────────────────────────────────────────────────────

def _list_tools_sse() -> List[Dict[str, Any]]:
    """Fetch tools from the MCP server using the SSE protocol."""
    from mcp.client.sse import sse_client
    from mcp import ClientSession

    sse_url = _mcp_url() + "/sse"

    async def _fetch():
        async with sse_client(sse_url, timeout=15) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                tools = []
                for tool in result.tools:
                    tool_dict = {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": {},
                    }
                    if tool.inputSchema:
                        tool_dict["parameters"] = tool.inputSchema
                    tools.append(tool_dict)
                return tools

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_fetch())
    finally:
        loop.close()


# ── REST approach (original) ──────────────────────────────────────────────────

def _list_tools_rest() -> List[Dict[str, Any]]:
    """Fetch tools via the /tools REST endpoint (requires server support)."""
    resp = requests.get(f"{_mcp_url()}/tools", timeout=10)
    resp.raise_for_status()
    return resp.json()


# ── Public API ────────────────────────────────────────────────────────────────

def list_tools() -> List[Dict[str, Any]]:
    """Fetch the list of registered MCP tools with descriptions and parameters."""
    if _USE_SSE:
        return _list_tools_sse()
    return _list_tools_rest()


def check_health() -> bool:
    """Return True if the MCP server is reachable."""
    try:
        if _USE_SSE:
            resp = requests.get(f"{_mcp_url()}/sse", timeout=5, stream=True)
            resp.close()
            return resp.status_code == 200
        else:
            resp = requests.get(f"{_mcp_url()}/health", timeout=5)
            return resp.status_code == 200
    except Exception:
        return False
