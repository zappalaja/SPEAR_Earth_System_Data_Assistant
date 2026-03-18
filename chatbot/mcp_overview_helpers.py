"""
mcp_overview_helpers.py — API client functions for the MCP Tools Overview page.

Calls the MCP server's /tools REST endpoint (default http://localhost:8000).
"""

import os
import requests
from typing import Any, Dict, List


def _mcp_url() -> str:
    return os.getenv("MCP_SERVER_URL", "http://localhost:8000").rstrip("/")


def list_tools() -> List[Dict[str, Any]]:
    """Fetch the list of registered MCP tools with descriptions and parameters."""
    resp = requests.get(f"{_mcp_url()}/tools", timeout=10)
    resp.raise_for_status()
    return resp.json()


def check_health() -> bool:
    """Return True if the MCP server is reachable."""
    try:
        resp = requests.get(f"{_mcp_url()}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False
