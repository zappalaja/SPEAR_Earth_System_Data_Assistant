"""Server creation with FastMCP and tool registration.

Tools are organized into three groups:
  - S3 directory browsing tools (tools.py) — always enabled
  - NetCDF tools (tools_nc.py) — enabled when ENABLE_NETCDF_TOOLS=true
  - ArrayLake Zarr tools (tools_arraylake.py) — always enabled

Set ENABLE_NETCDF_TOOLS=true in your environment or .env to re-enable the
legacy NetCDF tools alongside ArrayLake.
"""

import argparse
import asyncio
import os

from fastmcp import FastMCP
from loguru import logger
from starlette.requests import Request
from starlette.responses import PlainTextResponse, JSONResponse

from . import tools, tools_arraylake

# NetCDF tools are opt-in via environment variable
ENABLE_NETCDF_TOOLS = os.environ.get("ENABLE_NETCDF_TOOLS", "false").lower() in ("true", "1", "yes")
ENABLE_ARRAYLAKE_TOOLS = os.environ.get("ENABLE_ARRAYLAKE_TOOLS", "true").lower() in ("true", "1", "yes")
if ENABLE_NETCDF_TOOLS:
    from . import tools_nc

# Legacy CMIP6-only Zarr tools (fully replaced by ArrayLake)
# from . import tools_zarr

##############################################################################################
##############################################################################################
# Add or remove tools as needed.
async def create_server() -> FastMCP:
    """Create and configure the MCP server and register tools"""
    mcp = FastMCP('SPEAR Earth System Data Assistant MCP Server')

    # ========== S3 DIRECTORY BROWSING TOOLS (always enabled) ==========
    mcp.tool()(tools.validate_spear_url)
    """
    Check that the SPEAR url is still live and reachable.
    """

    mcp.tool()(tools.browse_spear_directory)
    """
    Dynamically browse SPEAR directory structure step by step.
    Starts with 'empty' path and then navigates deeper by providing path components.
    Example: browse_spear_directory("historical/r1i1p1f1/Amon")
    """

    mcp.tool()(tools.navigate_spear_path)
    """
    Build and navigate to a specific SPEAR path by combining path components.
    Useful for building complete paths step by step.
    Example: navigate_spear_path(["historical", "r1i1p1f1", "Amon"])
    """

    mcp.tool()(tools.search_spear_variables)
    """
    Search for variables across SPEAR datasets matching given criteria.
    Useful for finding specific climate variables across runs and frequencies.
    Example: search_spear_variables("historical", "tas", "Amon")
    """

    # ========== NETCDF TOOLS (opt-in via ENABLE_NETCDF_TOOLS=true) ==========
    if ENABLE_NETCDF_TOOLS:
        logger.info("NetCDF tools ENABLED (ENABLE_NETCDF_TOOLS=true)")

        mcp.tool()(tools_nc.make_json_serializable)
        """
        Recursively convert objects to JSON-serializable format. Handles numpy arrays,
        cftime objects, and nested data structures. Essential helper for returning
        complex scientific data through the MCP protocol.
        """

        mcp.tool()(tools_nc.convert_cftime_to_string)
        """
        Convert cftime datetime objects to ISO format strings for JSON compatibility.
        Handles various cftime calendar types (Julian, Gregorian, NoLeap, 360Day).
        """

        mcp.tool()(tools_nc.test_spear_connection)
        """
        Test basic S3 connection to SPEAR bucket and return sample file listings.
        Useful for development and debugging S3 connectivity issues.
        """

        mcp.tool()(tools_nc.get_file_info_and_validation)
        """
        Get comprehensive file information including metadata, dimensions, time ranges,
        and spatial coverage. Returns validation data for verifying query parameters
        against actual file contents.
        Example: get_file_info_and_validation("historical", "r1i1p1f1", "Amon", "tas")
        """

        mcp.tool()(tools_nc.validate_query_parameters)
        """
        Validate query parameters (dates, spatial ranges, variables) against actual
        file data ranges. Returns validation status, errors, and warnings before
        attempting data queries.
        """

        mcp.tool()(tools_nc.estimate_response_size)
        """
        Estimate response size in bytes for given data shape and dtype. Used to
        determine if data needs chunking to stay within MCP response limits (~1MB).
        """

        mcp.tool()(tools_nc.calculate_chunk_size)
        """
        Calculate optimal chunk dimensions to keep responses under size limits.
        Returns chunking strategy and estimated chunk count for large datasets.
        Prioritizes time-dimension chunking for 3D climate data.
        """

        mcp.tool()(tools_nc.load_dataset_if_needed)
        """
        Load NetCDF dataset into memory cache if not already loaded. Maintains
        global cache to avoid repeated S3 reads for the same file. Returns
        cached xarray Dataset object.
        """

        mcp.tool()(tools_nc.query_netcdf_data)
        """
        Query NetCDF data with spatial/temporal subsetting and automatic chunking.
        Main data extraction tool - handles parameter validation, spatial/temporal
        slicing, chunking for large responses, and JSON serialization.
        Example: query_netcdf_data("tas", "2020-01", "2021-12", [30, 50], [-120, -80])
        """

        mcp.tool()(tools_nc.get_data_summary_statistics)
        """
        Get summary statistics for data selections without returning full arrays.
        Currently returns basic shape and size information. Statistical calculations
        are still in development.
        """

        mcp.tool()(tools_nc.get_s3_file_metadata_only)
        """
        Extract only file metadata without loading data arrays. Returns dimensions,
        coordinates, variable information, and attributes. Efficient for exploring
        file structure without memory overhead.
        Example: get_s3_file_metadata_only("scenarioSSP5-85", "r15i1p1f1", "Amon", "pr")
        """
    else:
        logger.info("NetCDF tools DISABLED (set ENABLE_NETCDF_TOOLS=true to enable)")

    # ========== ARRAYLAKE TOOLS (SPEAR Zarr v3 — opt-out via ENABLE_ARRAYLAKE_TOOLS=false) ==========
    if ENABLE_ARRAYLAKE_TOOLS:
        logger.info("ArrayLake tools ENABLED (ENABLE_ARRAYLAKE_TOOLS=true)")

        mcp.tool()(tools_arraylake.test_arraylake_connection)
        """
        Test connection to the SPEAR ArrayLake repository. With no arguments,
        opens the repo root and lists top-level groups/arrays. With a group path,
        opens that group as an xarray Dataset and returns dimensions/variables.
        Example: test_arraylake_connection()  OR  test_arraylake_connection("historical/Amon")
        """

        mcp.tool()(tools_arraylake.browse_arraylake_repo)
        """
        Browse the Zarr hierarchy in the SPEAR ArrayLake repository. Lists child
        groups and arrays starting from a given path (or root). Use this to
        discover the repo layout before querying data.
        Example: browse_arraylake_repo()  OR  browse_arraylake_repo("historical", max_depth=3)
        """

        mcp.tool()(tools_arraylake.get_arraylake_store_info)
        """
        Get metadata from a SPEAR Zarr group on ArrayLake without loading data.
        Returns dimensions, variables, and optionally full coordinate details.
        Example: get_arraylake_store_info("historical/Amon", include_full_details=True)
        """

        mcp.tool()(tools_arraylake.query_arraylake_data)
        """
        Query SPEAR Zarr data on ArrayLake with spatial/temporal/ensemble subsetting.
        Main data extraction tool - handles coordinate conversion, member selection,
        and JSON serialization. 50 MB response cap.
        Example: query_arraylake_data("tas", "historical/Amon", member_id=1, start_date="1921-01", end_date="2014-12", lat_range=[30, 50], lon_range=[-120, -80])
        """

        mcp.tool()(tools_arraylake.get_arraylake_summary_statistics)
        """
        Get summary statistics (min, max, mean, std) for SPEAR data on ArrayLake
        without returning full arrays. More efficient than loading all data.
        Example: get_arraylake_summary_statistics("tas", "historical/Amon", member_id=1, start_date="1921-01", end_date="2014-12")
        """
    else:
        logger.info("ArrayLake tools DISABLED (set ENABLE_ARRAYLAKE_TOOLS=true to enable)")

    # ========== LEGACY ZARR TOOLS (CMIP6 single-collection, fully replaced) ==========
    # mcp.tool()(tools_zarr.test_cmip6_connection)
    # mcp.tool()(tools_zarr.get_zarr_store_info)
    # mcp.tool()(tools_zarr.load_zarr_dataset)
    # mcp.tool()(tools_zarr.query_zarr_data)
    # mcp.tool()(tools_zarr.get_zarr_summary_statistics)

    # Future Tools! Coming soon!
    # mcp.tool()(tools_nc.get_catalog_file_metadata_only)


##############################################################################################
##############################################################################################
# Residual functions. Will explore more in depth.

    # Add health check endpoint, mainly for Docker purposes.
    @mcp.custom_route('/health', methods=['GET'])
    async def health_check(request: Request) -> PlainTextResponse:
        return PlainTextResponse('OK')

    # Expose registered tools as a REST endpoint for the Streamlit UI.
    @mcp.custom_route('/tools', methods=['GET'])
    async def list_tools(request: Request) -> JSONResponse:
        tool_list = []
        tools = await mcp.list_tools()
        for t in tools:
            tool_list.append({
                "name": t.name,
                "description": t.description or "",
                "parameters": t.parameters,
            })
        return JSONResponse(tool_list)

    return mcp

async def async_main(transport: str, host: str, port: int):
    # Disable logging for stdio transport to avoid interfering with MCP protocol.
    if transport == 'stdio':
        logger.remove()
        logger.add(lambda _: None)

    server = await create_server()
    logger.info('Server created with enhanced SPEAR navigation tools')
    if transport == 'stdio':
        await server.run_async(transport='stdio')
    elif transport in ['http', 'sse']:
        # Configure uvicorn with extended timeouts for large S3 data transfers
        uvicorn_config = {
            "timeout_keep_alive": 1800,  # 30 minutes keep-alive timeout
        }
        await server.run_async(transport=transport, host=host, port=port, uvicorn_config=uvicorn_config)


def main():
    parser = argparse.ArgumentParser(
        description='Test server for SPEAR NetCDF Public data with dynamic navigation.'
    )
    parser.add_argument(
        '--transport',
        choices=['stdio', 'http', 'sse'],
        default='sse',
        help='Transport protocol to use (default: sse for HTTP mode)',
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to for http/sse transport (default: 0.0.0.0 for container access)',
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to bind to for http/sse transport (default: 8000)',
    )

    args = parser.parse_args()

    # Limit what host can be
    allowed_hosts = ['127.0.0.1', 'localhost', '0.0.0.0']
    if args.host not in allowed_hosts:
        raise ValueError(f"Host '{args.host}' not allowed. Use one of: {allowed_hosts}")

    # A separate sync main function is needed because it is the entry point
    asyncio.run(async_main(args.transport, args.host, args.port))
