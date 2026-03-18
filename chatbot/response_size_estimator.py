"""
Response Size Estimator
========================

This module provides utilities to estimate the size of responses before executing
tools, preventing token limit errors and providing helpful alternatives.

Token Limits:
- Local Ollama model: 200,000 tokens maximum per request (configured assumption)
- Safe threshold: ~180,000 tokens (90% of limit)
- Reserve for response: ~20,000 tokens

Estimation Strategy:
- Estimate data array size based on dimensions
- Account for metadata, formatting, and overhead
- Suggest alternatives if request is too large
"""

import math
from typing import Dict, Tuple, Optional, List


# ============================================================================
# CONFIGURATION
# ============================================================================

# Token limits
MAX_TOKENS_PER_REQUEST = 200000
SAFE_TOKEN_THRESHOLD = 100000  # Much more conservative - 50% of max to account for conversation
RESPONSE_TOKEN_RESERVE = 30000  # Reserve for AI response and metadata

# Average characters per token (approximation)
CHARS_PER_TOKEN = 3  # More conservative (was 4)

# Bytes per data point by type
BYTES_PER_FLOAT32 = 4
BYTES_PER_FLOAT64 = 8

# Overhead multipliers for JSON formatting
JSON_OVERHEAD_MULTIPLIER = 2.5  # More conservative - JSON + metadata adds significant overhead (was 1.5)


# ============================================================================
# SIZE ESTIMATION FUNCTIONS
# ============================================================================

def estimate_data_array_size(shape: Tuple[int, ...], dtype: str = "float32") -> int:
    """
    Estimate the size in bytes of a data array.

    Args:
        shape: Dimensions of the array (e.g., (12, 180, 360) for time x lat x lon)
        dtype: Data type ("float32" or "float64")

    Returns:
        Estimated size in bytes
    """
    # Calculate total number of elements
    total_elements = math.prod(shape)

    # Get bytes per element
    bytes_per_element = BYTES_PER_FLOAT64 if dtype == "float64" else BYTES_PER_FLOAT32

    # Calculate raw data size
    raw_bytes = total_elements * bytes_per_element

    return raw_bytes


def estimate_json_size(raw_bytes: int, include_metadata: bool = True) -> int:
    """
    Estimate size of data when converted to JSON format.

    Args:
        raw_bytes: Raw data size in bytes
        include_metadata: Whether metadata is included

    Returns:
        Estimated JSON size in bytes
    """
    # JSON formatting adds overhead (commas, brackets, field names)
    json_bytes = int(raw_bytes * JSON_OVERHEAD_MULTIPLIER)

    # Add metadata overhead (coordinates, dimensions, attributes)
    if include_metadata:
        metadata_overhead = 5000  # ~5KB for typical metadata
        json_bytes += metadata_overhead

    return json_bytes


def estimate_tokens_from_bytes(size_bytes: int) -> int:
    """
    Estimate number of tokens from byte size.

    Args:
        size_bytes: Size in bytes

    Returns:
        Estimated number of tokens
    """
    # Convert bytes to characters (UTF-8, mostly ASCII for numbers)
    chars = size_bytes  # Roughly 1 byte per character for numbers

    # Convert characters to tokens
    tokens = chars // CHARS_PER_TOKEN

    return tokens


def estimate_query_tokens(
    time_points: int,
    lat_points: int,
    lon_points: int,
    dtype: str = "float32",
    include_metadata: bool = True
) -> int:
    """
    Estimate total tokens for a NetCDF data query.

    Args:
        time_points: Number of time steps
        lat_points: Number of latitude points
        lon_points: Number of longitude points
        dtype: Data type
        include_metadata: Whether metadata is included

    Returns:
        Estimated number of tokens
    """
    # Calculate array shape
    shape = (time_points, lat_points, lon_points)

    # Estimate sizes
    raw_bytes = estimate_data_array_size(shape, dtype)
    json_bytes = estimate_json_size(raw_bytes, include_metadata)
    tokens = estimate_tokens_from_bytes(json_bytes)

    return tokens


# ============================================================================
# SIZE CHECKING AND RECOMMENDATIONS
# ============================================================================

def is_query_too_large(
    time_points: int,
    lat_points: int,
    lon_points: int,
    current_conversation_tokens: int = 0
) -> Tuple[bool, int, str]:
    """
    Check if a query would exceed token limits.

    Args:
        time_points: Number of time steps
        lat_points: Number of latitude points
        lon_points: Number of longitude points
        current_conversation_tokens: Tokens already in conversation

    Returns:
        Tuple of (is_too_large, estimated_tokens, message)
    """
    # Estimate query size
    estimated_tokens = estimate_query_tokens(time_points, lat_points, lon_points)

    # Calculate total tokens needed
    total_tokens = current_conversation_tokens + estimated_tokens + RESPONSE_TOKEN_RESERVE

    # Check if too large
    is_too_large = total_tokens > SAFE_TOKEN_THRESHOLD

    # Generate message
    if is_too_large:
        message = f"This query would generate approximately {estimated_tokens:,} tokens"
        message += f" (total: {total_tokens:,} tokens), which exceeds the safe limit of {SAFE_TOKEN_THRESHOLD:,} tokens."
    else:
        message = f"✓ Query size is acceptable: ~{estimated_tokens:,} tokens"

    return is_too_large, estimated_tokens, message


def suggest_alternatives(
    time_points: int,
    lat_points: int,
    lon_points: int,
    variable: str,
    scenario: str,
    ensemble: str
) -> Dict[str, any]:
    """
    Suggest alternative approaches when a query is too large.

    Args:
        time_points, lat_points, lon_points: Original request dimensions
        variable, scenario, ensemble: Query parameters

    Returns:
        Dictionary with suggestions
    """
    suggestions = {
        "problem": f"Requested data ({time_points} time × {lat_points} lat × {lon_points} lon = {time_points * lat_points * lon_points:,} points) is too large",
        "alternatives": []
    }

    # Calculate target size (50% of current for safety)
    target_points = (time_points * lat_points * lon_points) // 2

    # Suggestion 1: Reduce time range
    if time_points > 12:
        reduced_time = max(12, time_points // 2)
        time_reduction = estimate_query_tokens(reduced_time, lat_points, lon_points)
        suggestions["alternatives"].append({
            "approach": "Reduce time range",
            "description": f"Request {reduced_time} time steps instead of {time_points}",
            "example": f"Try: 'Show me data for 2020-2025' instead of the full period",
            "estimated_tokens": time_reduction
        })

    # Suggestion 2: Reduce spatial coverage
    if lat_points > 10 or lon_points > 10:
        reduced_lat = max(5, lat_points // 2)
        reduced_lon = max(5, lon_points // 2)
        spatial_reduction = estimate_query_tokens(time_points, reduced_lat, reduced_lon)
        suggestions["alternatives"].append({
            "approach": "Reduce spatial coverage",
            "description": f"Request smaller region ({reduced_lat}×{reduced_lon} instead of {lat_points}×{lon_points})",
            "example": "Try: 'Show me data for the Northeast US' instead of entire globe",
            "estimated_tokens": spatial_reduction
        })

    # Suggestion 3: Spatial averaging
    suggestions["alternatives"].append({
        "approach": "Request spatial average",
        "description": "Get area-averaged value instead of full grid",
        "example": f"Try: 'What is the average {variable} over this region?'",
        "estimated_tokens": time_points * 100  # Just time series
    })

    # Suggestion 4: Use monthly instead of daily
    if time_points > 365:  # Likely daily data
        monthly_time = time_points // 30
        monthly_reduction = estimate_query_tokens(monthly_time, lat_points, lon_points)
        suggestions["alternatives"].append({
            "approach": "Use monthly averages instead of daily",
            "description": f"Request monthly data (~{monthly_time} points) instead of daily",
            "example": "Specify monthly frequency (Amon) instead of daily",
            "estimated_tokens": monthly_reduction
        })

    # Suggestion 5: Download programmatically
    suggestions["alternatives"].append({
        "approach": "Download data programmatically",
        "description": "For large datasets, use Python code to access data directly",
        "code_example": f"""
# Python code to access SPEAR data directly
import xarray as xr

# Open dataset from S3
ds = xr.open_dataset(
    's3://noaa-gfdl-spear-{scenario}/...',
    storage_options={{'anon': True}}
)

# Select your variable and region
data = ds['{variable}'].sel(
    ensemble='{ensemble}',
    time=slice('2020-01-01', '2100-12-31'),
    lat=slice(35, 45),
    lon=slice(-80, -70)
)

# Compute statistics or save
result = data.mean(dim=['lat', 'lon'])
result.to_netcdf('output.nc')
""",
        "estimated_tokens": 0  # No tokens used in chat
    })

    return suggestions


# ============================================================================
# FORMATTING HELPERS
# ============================================================================

def format_size_warning(
    estimated_tokens: int,
    suggestions: Dict
) -> str:
    """
    Format a user-friendly warning message with alternatives.

    Args:
        estimated_tokens: Estimated token count
        suggestions: Dictionary of alternative approaches

    Returns:
        Formatted markdown message
    """
    message = f"""## Response Too Large

This query would generate approximately **{estimated_tokens:,} tokens**, which exceeds the safe limit for our conversation.

{suggestions['problem']}

### Suggested Alternatives:

"""

    for i, alt in enumerate(suggestions['alternatives'], 1):
        message += f"**{i}. {alt['approach']}**\n"
        message += f"   - {alt['description']}\n"
        if 'example' in alt:
            message += f"   - Example: *{alt['example']}*\n"
        if alt['estimated_tokens'] > 0:
            message += f"   - Estimated size: ~{alt['estimated_tokens']:,} tokens ✓\n"
        if 'code_example' in alt:
            message += f"\n```python{alt['code_example']}```\n"
        message += "\n"

    message += "### Tips:\n"
    message += "- Start with smaller regions and time periods\n"
    message += "- Use spatial/temporal averages when possible\n"
    message += "- For very large analyses, use Python scripts to access data directly\n"

    return message


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("Response Size Estimator - Test Cases")
    print("=" * 60)

    # Test case 1: Small query (should be OK)
    print("\n1. Small query (1 year, regional):")
    is_large, tokens, msg = is_query_too_large(
        time_points=12,  # 1 year monthly
        lat_points=10,   # 10° latitude
        lon_points=10,   # 10° longitude
        current_conversation_tokens=15000
    )
    print(f"   {msg}")
    print(f"   Too large: {is_large}")

    # Test case 2: Large query (should warn)
    print("\n2. Large query (80 years, global):")
    is_large, tokens, msg = is_query_too_large(
        time_points=960,  # 80 years monthly
        lat_points=180,   # Global latitude
        lon_points=360,   # Global longitude
        current_conversation_tokens=15000
    )
    print(f"   {msg}")
    print(f"   Too large: {is_large}")

    if is_large:
        print("\n   Suggestions:")
        suggestions = suggest_alternatives(960, 180, 360, "tas", "historical", "r1i1p1f1")
        for i, alt in enumerate(suggestions['alternatives'][:3], 1):
            print(f"   {i}. {alt['approach']}: {alt['description']}")

    print("\n" + "=" * 60)
    print("✓ Estimator ready to use")
