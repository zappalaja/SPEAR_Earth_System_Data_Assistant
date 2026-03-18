import sys
import os
import asyncio
import json
from datetime import datetime
from plotting_tool import plot_climate_data
from response_size_estimator import is_query_too_large, suggest_alternatives, format_size_warning

# MCP Client imports
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# ============================================================================
# DATA CACHE - Store query results to avoid re-querying
# ============================================================================
# Cache is stored per-session in st.session_state so that different users
# never share each other's results. Falls back to a plain dict when called
# outside a Streamlit context (e.g. tests or stdio transport mode).

def _get_cache() -> dict:
    try:
        import streamlit as st
        if "query_data_cache" not in st.session_state:
            st.session_state.query_data_cache = {}
        return st.session_state.query_data_cache
    except Exception:
        return {}

def get_cache_key(tool_name: str, tool_input: dict) -> str:
    """Generate a cache key from tool name and input parameters."""
    sorted_input = json.dumps(tool_input, sort_keys=True, default=str)
    return f"{tool_name}:{sorted_input}"

def get_cached_result(tool_name: str, tool_input: dict):
    """Check if we have a cached result for this query."""
    cache = _get_cache()
    cache_key = get_cache_key(tool_name, tool_input)
    if cache_key in cache:
        print(f"[CACHE HIT] Returning cached result for {tool_name}")
        return cache[cache_key]
    return None

def cache_result(tool_name: str, tool_input: dict, result: dict):
    """Store a result in the cache."""
    cache = _get_cache()
    cache_key = get_cache_key(tool_name, tool_input)
    cache[cache_key] = result
    print(f"[CACHE STORE] Cached result for {tool_name} (cache size: {len(cache)})")

def get_last_query_data() -> dict:
    """Get the most recent query_netcdf_data result for plotting."""
    cache = _get_cache()
    for key in reversed(list(cache.keys())):
        if key.startswith("query_netcdf_data:"):
            return cache[key]
    return None

# Check if we should use HTTP or stdio transport
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
USE_HTTP_TRANSPORT = MCP_SERVER_URL is not None

if USE_HTTP_TRANSPORT:
    print(f"[MCP CONFIG] Using HTTP SSE transport to: {MCP_SERVER_URL}")
    from mcp.client.sse import sse_client
    print("[MCP CONFIG] SSE client imported successfully")
else:
    # MCP Server configuration - using stdio transport (local development fallback)
    # Set MCP_SERVER_DIR in .env to override; defaults to ../mcp-server relative to this file
    _default_mcp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp-server")
    _mcp_server_dir = os.getenv("MCP_SERVER_DIR", _default_mcp_dir)
    print(f"[MCP CONFIG] Using stdio transport (local development): {_mcp_server_dir}")
    MCP_SERVER_PARAMS = StdioServerParameters(
        command="uv",
        args=["--directory", _mcp_server_dir, "run", "spear-mcp"]
    )

# Define available tools with their metadata
AVAILABLE_TOOLS = [
    {
        "name": "create_plot",
        "description": "Create and display a matplotlib plot",
        "function": plot_climate_data
    },
    # All paths, variables, and file mappings are precomputed in spear_data_paths.py.
    # The bot should use query_netcdf_data DIRECTLY without browsing or searching.
    {
        "name": "get_s3_file_metadata_only",
        "description": "Get metadata of a SPEAR NetCDF file without loading data",
        "mcp_tool": True
    },
    {
        "name": "query_netcdf_data",
        "description": "Query NetCDF data with spatial/temporal subsetting",
        "mcp_tool": True
    },
    # CMIP6 Zarr tools
    {
        "name": "test_cmip6_connection",
        "description": "Test connection to CMIP6 Zarr store",
        "mcp_tool": True
    },
    {
        "name": "get_zarr_store_info",
        "description": "Get metadata about the CMIP6 Zarr store",
        "mcp_tool": True
    },
    {
        "name": "query_zarr_data",
        "description": "Query CMIP6 Zarr data with spatial/temporal subsetting",
        "mcp_tool": True
    },
    {
        "name": "get_zarr_summary_statistics",
        "description": "Get summary statistics from CMIP6 Zarr data",
        "mcp_tool": True
    }
]


# ============================================================================
# RESPONSE SIZE CHECKING FUNCTIONS
# ============================================================================

def parse_time_range(start_date, end_date, frequency="Amon"):
    """
    Calculate number of time points from date range.

    Args:
        start_date: Start date string (YYYY-MM or YYYY-MM-DD)
        end_date: End date string (YYYY-MM or YYYY-MM-DD)
        frequency: Data frequency (default: Amon for monthly)

    Returns:
        Number of time points
    """
    if not start_date or not end_date:
        # If no dates provided, assume worst case (full historical + SSP5-85)
        # Historical: 1850-2014 (165 years)
        # SSP5-85: 2015-2100 (86 years)
        # Total: 251 years
        if frequency == "Amon":
            return 251 * 12  # ~3000 monthly time points
        elif frequency == "day":
            return 251 * 365  # ~91,000 daily time points
        else:
            return 251 * 12  # Default to monthly

    # Parse year and month from dates
    from datetime import datetime

    try:
        # Handle YYYY-MM format
        if len(start_date) == 7:  # YYYY-MM
            start = datetime.strptime(start_date, "%Y-%m")
            end = datetime.strptime(end_date, "%Y-%m")
        else:  # YYYY-MM-DD
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

        # Calculate time difference
        years = (end.year - start.year)
        months = (end.month - start.month)
        total_months = years * 12 + months + 1  # +1 to include end month

        # Convert to time points based on frequency
        if frequency == "Amon":
            return total_months
        elif frequency == "day":
            return total_months * 30  # Approximate days
        else:
            return total_months
    except:
        # If parsing fails, return conservative estimate
        return 1000


def estimate_spatial_points(lat_range, lon_range):
    """
    Estimate number of grid points from lat/lon ranges.

    Args:
        lat_range: [min_lat, max_lat] or None
        lon_range: [min_lon, max_lon] or None

    Returns:
        (lat_points, lon_points)
    """
    # SPEAR_MED resolution is approximately 1 degree
    SPEAR_LAT_RESOLUTION = 1.0  # degrees
    SPEAR_LON_RESOLUTION = 1.0  # degrees

    if lat_range is None or lon_range is None:
        # Global grid
        return 180, 360

    # Calculate points from ranges
    lat_points = int(abs(lat_range[1] - lat_range[0]) / SPEAR_LAT_RESOLUTION)
    lon_points = int(abs(lon_range[1] - lon_range[0]) / SPEAR_LON_RESOLUTION)

    # Ensure at least 1 point
    lat_points = max(1, lat_points)
    lon_points = max(1, lon_points)

    return lat_points, lon_points


def check_query_size_before_execution(tool_input):
    """
    Check if a query_netcdf_data query would be too large.
    Returns None if query is OK, or error response if too large.

    Args:
        tool_input: Dictionary with query parameters

    Returns:
        None if OK, or dict with error/warning if too large
    """
    # Extract parameters from tool input
    start_date = tool_input.get("start_date")
    end_date = tool_input.get("end_date")
    lat_range = tool_input.get("lat_range")
    lon_range = tool_input.get("lon_range")
    frequency = tool_input.get("frequency", "Amon")
    variable = tool_input.get("variable", "unknown")
    scenario = tool_input.get("scenario", "scenarioSSP5-85")
    ensemble = tool_input.get("ensemble_member", "r1i1p1f1")

    # ========================================================================
    # VALIDATE AND AUTO-CONVERT LAT/LON RANGES
    # ========================================================================
    # SPEAR grid ranges:
    # - Latitude: -89.5 to 89.5 (valid range)
    # - Longitude: 0.3125 to 359.6875 (0-360 format, NOT -180 to 180!)

    conversion_notes = []

    # Validate and fix latitude
    if lat_range is not None:
        min_lat, max_lat = lat_range
        if min_lat < -90 or max_lat > 90:
            return {
                "status": "error",
                "error": "Invalid latitude range",
                "warning_message": f"**Invalid Latitude Range**\n\nLatitude must be between -90 and 90 degrees.\nYou provided: {lat_range}"
            }
        if min_lat >= max_lat:
            return {
                "status": "error",
                "error": "Invalid latitude range",
                "warning_message": f"**Invalid Latitude Range**\n\nmin_lat must be less than max_lat.\nYou provided: {lat_range}"
            }

    # Auto-convert longitude from -180/180 to 0-360 format
    if lon_range is not None:
        min_lon, max_lon = lon_range
        original_range = lon_range.copy() if isinstance(lon_range, list) else list(lon_range)

        # Convert negative longitudes to 0-360
        if min_lon < 0:
            min_lon = min_lon + 360
            conversion_notes.append(f"Converted min_lon: {original_range[0]}° → {min_lon}°")
        if max_lon < 0:
            max_lon = max_lon + 360
            conversion_notes.append(f"Converted max_lon: {original_range[1]}° → {max_lon}°")

        # Update tool_input with converted values
        tool_input["lon_range"] = [min_lon, max_lon]

        # Validate final range
        if min_lon > 360 or max_lon > 360:
            return {
                "status": "error",
                "error": "Invalid longitude range",
                "warning_message": f"**Invalid Longitude Range**\n\nLongitude must be between 0 and 360 degrees.\nConverted range: [{min_lon}, {max_lon}]"
            }

    # Log conversions for debugging
    if conversion_notes:
        print(f"[COORDINATE CONVERSION] {'; '.join(conversion_notes)}")  # DEBUG

    # Calculate dimensions
    time_points = parse_time_range(start_date, end_date, frequency)
    lat_points, lon_points = estimate_spatial_points(lat_range, lon_range)

    # Check if too large (use function from response_size_estimator)
    is_too_large, estimated_tokens, message = is_query_too_large(
        time_points,
        lat_points,
        lon_points,
        current_conversation_tokens=15000  # Conservative estimate
    )

    if is_too_large:
        # Generate suggestions
        suggestions = suggest_alternatives(
            time_points,
            lat_points,
            lon_points,
            variable,
            scenario,
            ensemble
        )

        # Format warning message
        warning = format_size_warning(estimated_tokens, suggestions)

        # Return as error response (prevents tool execution)
        return {
            "status": "error",
            "error": "Query too large - response would exceed token limits",
            "warning_message": warning,
            "estimated_tokens": estimated_tokens,
            "data_shape": {
                "time_points": time_points,
                "lat_points": lat_points,
                "lon_points": lon_points,
                "total_data_points": time_points * lat_points * lon_points
            },
            "suggestions": suggestions
        }

    # Query size is acceptable - return None to proceed with execution
    return None


def preprocess_query_parameters(tool_input):
    """
    Preprocess query_netcdf_data parameters to fix common issues:
    1. Convert negative longitudes (-180 to 180) to 0-360 format
    2. Ensure lat/lon ranges are in correct order [min, max]
    3. Set sensible defaults for missing parameters
    """
    import copy
    processed = copy.deepcopy(tool_input)

    # ========================================================================
    # FIX LONGITUDE FORMAT: Convert -180/180 to 0-360
    # ========================================================================
    lon_range = processed.get("lon_range")
    if lon_range is not None and isinstance(lon_range, list) and len(lon_range) == 2:
        min_lon, max_lon = lon_range
        original = [min_lon, max_lon]

        # Convert negative longitudes to 0-360
        if min_lon < 0:
            min_lon = min_lon + 360
        if max_lon < 0:
            max_lon = max_lon + 360

        # Ensure proper ordering
        if min_lon > max_lon:
            min_lon, max_lon = max_lon, min_lon

        processed["lon_range"] = [min_lon, max_lon]

        if original != [min_lon, max_lon]:
            print(f"[PREPROCESS] Converted lon_range: {original} -> {processed['lon_range']}")

    # ========================================================================
    # FIX LATITUDE ORDER: Ensure [min, max]
    # ========================================================================
    lat_range = processed.get("lat_range")
    if lat_range is not None and isinstance(lat_range, list) and len(lat_range) == 2:
        min_lat, max_lat = lat_range
        if min_lat > max_lat:
            processed["lat_range"] = [max_lat, min_lat]
            print(f"[PREPROCESS] Fixed lat_range order: {lat_range} -> {processed['lat_range']}")

    # ========================================================================
    # SET DEFAULTS for commonly missing parameters
    # ========================================================================
    if not processed.get("ensemble_member"):
        processed["ensemble_member"] = "r1i1p1f1"
        print(f"[PREPROCESS] Set default ensemble_member: r1i1p1f1")

    if not processed.get("frequency"):
        processed["frequency"] = "Amon"
        print(f"[PREPROCESS] Set default frequency: Amon")

    if not processed.get("grid"):
        processed["grid"] = "gr3"

    if not processed.get("version"):
        processed["version"] = "v20210201"

    if not processed.get("scenario"):
        processed["scenario"] = "historical"
        print(f"[PREPROCESS] Set default scenario: historical")

    return processed


async def call_mcp_server_http(tool_name, tool_input):
    """Call the MCP server using SSE transport (proper MCP protocol)"""
    import traceback
    import time

    try:
        # Build the SSE URL (e.g., http://localhost:8000 -> http://localhost:8000/sse)
        sse_url = MCP_SERVER_URL.rstrip('/') + '/sse'
        print(f"[MCP] Connecting via SSE to: {sse_url}")
        print(f"[MCP] Tool: {tool_name}, Input: {tool_input}")

        # Track timing
        start_time = time.time()

        # Use the proper MCP SSE client with very long timeout for large S3 operations (6hr data)
        async with sse_client(sse_url, timeout=1800) as (read, write):  # 30 minutes
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                print(f"[MCP] Session initialized successfully")

                # Call the tool
                result = await session.call_tool(tool_name, tool_input)

                # Calculate elapsed time
                elapsed_time = time.time() - start_time
                print(f"[MCP] Tool call completed in {elapsed_time:.2f}s")

                # Extract content from result
                raw_content = ""
                if result.content:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        raw_content = content.text
                        data = raw_content
                        # Try to parse as JSON if possible
                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            pass
                    else:
                        data = str(content)
                        raw_content = data
                else:
                    data = "No content returned"
                    raw_content = ""

                # Calculate response size
                response_bytes = len(raw_content.encode('utf-8')) if raw_content else 0

                # Calculate data points if this is query_netcdf_data
                data_points = 0
                if tool_name == "query_netcdf_data" and isinstance(data, dict):
                    data_info = data.get("data_info", {})
                    shape = data_info.get("shape", [])
                    if shape:
                        data_points = 1
                        for dim in shape:
                            data_points *= dim

                return {
                    "status": "ok",
                    "tool": tool_name,
                    "data": data,
                    "transfer_stats": {
                        "elapsed_time_seconds": round(elapsed_time, 2),
                        "response_bytes": response_bytes,
                        "response_kb": round(response_bytes / 1024, 2),
                        "data_points": data_points,
                    }
                }

    except Exception as e:
        import sys
        error_trace = traceback.format_exc()
        sys.stderr.write(f"[MCP ERROR] {error_trace}\n")
        sys.stderr.flush()
        return {
            "status": "error",
            "error": f"Failed to connect to MCP server: {str(e)}",
            "traceback": error_trace
        }


async def call_mcp_server_stdio(tool_name, tool_input):
    """Call the MCP server using stdio transport"""
    import time

    try:
        # Track timing
        start_time = time.time()

        async with stdio_client(MCP_SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()

                # Call the tool
                result = await session.call_tool(tool_name, tool_input)

                # Calculate elapsed time
                elapsed_time = time.time() - start_time

                # Extract content from result
                raw_content = ""
                if result.content:
                    # Handle different content types
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        raw_content = content.text
                        data = raw_content
                        # Try to parse as JSON if possible
                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            pass
                    else:
                        data = str(content)
                        raw_content = data
                else:
                    data = "No content returned"
                    raw_content = ""

                # Calculate response size
                response_bytes = len(raw_content.encode('utf-8')) if raw_content else 0

                # Calculate data points if this is query_netcdf_data
                data_points = 0
                if tool_name == "query_netcdf_data" and isinstance(data, dict):
                    data_info = data.get("data_info", {})
                    shape = data_info.get("shape", [])
                    if shape:
                        data_points = 1
                        for dim in shape:
                            data_points *= dim

                return {
                    "status": "ok",
                    "tool": tool_name,
                    "data": data,
                    "transfer_stats": {
                        "elapsed_time_seconds": round(elapsed_time, 2),
                        "response_bytes": response_bytes,
                        "response_kb": round(response_bytes / 1024, 2),
                        "data_points": data_points,
                    }
                }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to connect to MCP server via stdio: {str(e)}"
        }


async def call_mcp_server(tool_name, tool_input):
    """Call the MCP server using configured transport (HTTP or stdio)"""
    if USE_HTTP_TRANSPORT:
        result = await call_mcp_server_http(tool_name, tool_input)
    else:
        result = await call_mcp_server_stdio(tool_name, tool_input)

    return result


async def query_mcp_tool_async(tool_name, tool_input):
    """Execute a SPEAR tool via MCP server or locally."""
    try:
        import inspect

        # Find the tool
        tool_config = None
        for tool in AVAILABLE_TOOLS:
            if tool["name"] == tool_name:
                tool_config = tool
                break

        if tool_config is None:
            return {
                "status": "error",
                "error": f"Unknown tool: {tool_name}"
            }

        # Check if this is an MCP tool
        if tool_config.get("mcp_tool", False):
            # Preprocess query_netcdf_data to fix common issues
            if tool_name == "query_netcdf_data":
                tool_input = preprocess_query_parameters(tool_input)

                # Check cache FIRST before making MCP call
                cached = get_cached_result(tool_name, tool_input)
                if cached:
                    # Add note that this is cached data
                    cached_copy = cached.copy()
                    if isinstance(cached_copy.get("data"), dict):
                        cached_copy["data"]["_cached"] = True
                        cached_copy["data"]["_cache_note"] = "This data was retrieved from cache. Use create_plot to visualize it."
                    return cached_copy

            # Call MCP server
            result = await call_mcp_server(tool_name, tool_input)

            # Cache successful query_netcdf_data results
            if tool_name == "query_netcdf_data" and result.get("status") == "ok":
                cache_result(tool_name, tool_input, result)

            return result

        # For local tools, get the function
        tool_func = tool_config.get("function")
        if tool_func is None:
            return {
                "status": "error", 
                "error": f"No function defined for tool: {tool_name}"
            }

        # ========================================================================
        # RESPONSE SIZE CHECKING (BEFORE TOOL EXECUTION)
        # ========================================================================
        # For query_netcdf_data, check if response would be too large
        if tool_name == "query_netcdf_data":
            print(f"[SIZE CHECK] Checking query size for: {tool_input}")  # DEBUG
            size_check_result = check_query_size_before_execution(tool_input)
            if size_check_result is not None:
                # Query is too large - return warning instead of executing
                print(f"[SIZE CHECK] Query TOO LARGE - blocking execution")  # DEBUG
                return size_check_result
            print(f"[SIZE CHECK] Query size OK - proceeding with execution")  # DEBUG

        # Execute the tool (handle both async and sync functions)
        if inspect.iscoroutinefunction(tool_func):
            result = await tool_func(**tool_input)
        else:
            result = tool_func(**tool_input)

        # Convert result to JSON-serializable format
        if isinstance(result, dict):
            result_data = result
        else:
            result_data = result.to_dict() if hasattr(result, 'to_dict') else str(result)

        return {
            "status": "ok",
            "tool": tool_name,
            "data": result_data
        }

    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": f"Failed to execute tool '{tool_name}': {str(e)}",
            "traceback": traceback.format_exc()
        }


def get_available_tools():
    """Get list of available tools."""
    return {
        "status": "ok",
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"]
            }
            for tool in AVAILABLE_TOOLS
        ]
    }


def query_mcp_tool(tool_name, tool_input):
    """Synchronous wrapper for querying an MCP tool."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(query_mcp_tool_async(tool_name, tool_input))
    finally:
        loop.close()

