"""
MCP Tools — Browse all tools registered on the SPEAR MCP server.
"""

import os
import sys
import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

from shared_styles import apply_sidebar_background
apply_sidebar_background()

from mcp_overview_helpers import list_tools, check_health

# ── Auth gate ────────────────────────────────────────────────────────────────
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
if AUTH_ENABLED:
    if not st.session_state.get("authentication_status"):
        st.warning("Please log in from the main page to access MCP Tools.")
        st.stop()

# ── Sidebar profile ─────────────────────────────────────────────────────────
from auth_setup import render_sidebar_profile
render_sidebar_profile(page_key="mcp")

# ── Page config ──────────────────────────────────────────────────────────────
st.title("MCP Server Tools")
st.markdown(
    "Browse the tools available on the **SPEAR MCP server**. "
    "These tools are used by the LLM assistant to access SPEAR output via "
    "ArrayLake (Zarr v3), S3 navigation, and optionally NetCDF datasets."
)

# ── Server health ────────────────────────────────────────────────────────────
mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
if check_health():
    st.success(f"MCP server is reachable at `{mcp_url}`")
else:
    st.error(f"Cannot reach MCP server at `{mcp_url}`")
    st.info("Make sure the MCP server is running. Tools cannot be listed while the server is offline.")
    st.stop()

# ── Fetch and display tools ──────────────────────────────────────────────────
try:
    tools = list_tools()
except Exception as e:
    st.error(f"Failed to fetch tools: {e}")
    st.stop()

if not tools:
    st.info("No tools are currently registered on the MCP server.")
    st.stop()

st.markdown(f"**{len(tools)} tools registered**")
st.divider()

# Group tools by category based on naming conventions
CATEGORY_MAP = {
    "SPEAR Navigation": ["validate_spear_url", "browse_spear_directory", "navigate_spear_path", "search_spear_variables"],
    "ArrayLake (SPEAR Zarr)": ["test_arraylake_connection", "browse_arraylake_repo", "get_arraylake_store_info", "query_arraylake_data", "get_arraylake_summary_statistics"],
    "CMIP6 Zarr (Legacy)": ["test_cmip6_connection", "get_zarr_store_info", "load_zarr_dataset", "query_zarr_data", "get_zarr_summary_statistics"],
}

def get_category(tool_name: str) -> str:
    for cat, names in CATEGORY_MAP.items():
        if tool_name in names:
            return cat
    # Fallback: anything with "netcdf" or "nc" is NetCDF, otherwise uncategorized
    if "netcdf" in tool_name.lower() or "s3_file" in tool_name or tool_name in (
        "make_json_serializable", "convert_cftime_to_string", "test_spear_connection",
        "get_file_info_and_validation", "validate_query_parameters", "estimate_response_size",
        "calculate_chunk_size", "load_dataset_if_needed", "query_netcdf_data",
        "get_data_summary_statistics", "get_s3_file_metadata_only",
    ):
        return "SPEAR NetCDF Data"
    return "Other"

# Build grouped dict preserving order
from collections import OrderedDict
grouped: dict[str, list] = OrderedDict()
for tool in tools:
    cat = get_category(tool["name"])
    grouped.setdefault(cat, []).append(tool)

# Preferred display order
display_order = ["SPEAR Navigation", "ArrayLake (SPEAR Zarr)", "SPEAR NetCDF Data", "CMIP6 Zarr (Legacy)"]
for cat in display_order:
    if cat not in grouped:
        continue
    st.subheader(cat)
    if cat == "CMIP6 Zarr (Legacy)":
        st.warning("Legacy tools — replaced by ArrayLake integration.")
    for tool in grouped[cat]:
        with st.expander(f"`{tool['name']}`"):
            st.markdown(tool.get("description") or "*No description provided.*")

            params = tool.get("parameters", {})
            properties = params.get("properties", {})
            required = set(params.get("required", []))

            if properties:
                st.markdown("**Parameters:**")
                for pname, pinfo in properties.items():
                    ptype = pinfo.get("type", pinfo.get("anyOf", ""))
                    if isinstance(ptype, list):
                        ptype = " | ".join(str(t) for t in ptype)
                    default = pinfo.get("default")
                    req_badge = " *(required)*" if pname in required else ""
                    desc = pinfo.get("description", "")
                    default_str = f"  Default: `{default}`" if default is not None else ""

                    st.markdown(f"- **`{pname}`** (`{ptype}`){req_badge}{default_str}")
                    if desc:
                        st.caption(f"  {desc}")
            else:
                st.caption("No parameters.")
    st.divider()

# Show any uncategorized tools
for cat, cat_tools in grouped.items():
    if cat not in display_order:
        st.subheader(cat)
        for tool in cat_tools:
            with st.expander(f"`{tool['name']}`"):
                st.markdown(tool.get("description") or "*No description provided.*")
        st.divider()
