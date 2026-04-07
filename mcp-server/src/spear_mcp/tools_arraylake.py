"""MCP tool script for working with SPEAR Zarr data via ArrayLake (Icechunk).

Replaces direct S3 Zarr access with ArrayLake-managed repos, providing
versioned, authenticated access to SPEAR large-ensemble output stored
as Zarr v3.

Repo structure:
    root/
    ├── historical/
    │   ├── 6hr/    (6-hourly variables)
    │   ├── Amon/   (monthly atmospheric variables — tas, pr, ua, etc.)
    │   ├── Ofx/    (ocean fixed fields)
    │   ├── Omon/   (monthly ocean variables)
    │   ├── day/    (daily variables)
    │   └── fx/     (atmospheric fixed fields)
    └── scenarioSSP5-85/
        └── (same sub-groups)

    Data dimensions: (member_id: 30, time, [plev], lat: 360, lon: 576)

Authentication:
    Set the ARRAYLAKE_TOKEN environment variable, or run `arraylake auth login`
    to cache credentials at ~/.arraylake/token.json.  The Client() constructor
    picks up either automatically.
"""

from typing import Any, Dict, List, Optional, Union

import logging
import warnings

import numpy as np
import xarray as xr
import zarr

from .coord_utils import subset_spatial

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

# ── ArrayLake configuration ────────────────────────────────────────────────
ARRAYLAKE_REPO = "GFDL/noaa-gfdl-spear-large-ensembles-pds"
ARRAYLAKE_BRANCH = "main"

# ── Cached client / session / root ─────────────────────────────────────────
_client = None
_session = None
_root = None
_dataset_cache: Dict[str, xr.Dataset] = {}


# ── Internal helpers ───────────────────────────────────────────────────────

def _get_session():
    """Return a cached read-only ArrayLake session, creating one if needed."""
    global _client, _session
    if _session is not None:
        return _session

    from arraylake import Client

    _client = Client()
    repo = _client.get_repo(ARRAYLAKE_REPO)
    _session = repo.readonly_session(branch=ARRAYLAKE_BRANCH)
    logger.info(
        "ArrayLake session opened: repo=%s branch=%s",
        ARRAYLAKE_REPO,
        ARRAYLAKE_BRANCH,
    )
    return _session


def _get_root():
    """Return the cached Zarr v3 root group, creating one if needed."""
    global _root
    if _root is not None:
        return _root

    session = _get_session()
    _root = zarr.open_group(session.store, zarr_format=3, mode="r")
    return _root


def _open_dataset(group: Optional[str] = None) -> xr.Dataset:
    """Open (or return cached) xarray Dataset at a group path.

    Args:
        group: Zarr group path (e.g. "historical/Amon").
               If None or empty, opens at the root level.
    """
    cache_key = group or "__root__"
    if cache_key in _dataset_cache:
        return _dataset_cache[cache_key]

    session = _get_session()

    kwargs: Dict[str, Any] = {"consolidated": False}
    if group:
        kwargs["group"] = group

    ds = xr.open_zarr(session.store, **kwargs)
    _dataset_cache[cache_key] = ds
    return ds


def _select_members(
    data_var: xr.DataArray,
    member_id: Optional[Union[int, str, List[int], List[str]]] = None,
) -> xr.DataArray:
    """Select ensemble member(s) if the dimension exists.

    Accepts member IDs as:
      - Integers 1-30  (converted to "r1i1p1f1" .. "r30i1p1f1")
      - Strings like "r1i1p1f1"
      - A list of either

    Args:
        data_var: DataArray that may have a 'member_id' dimension.
        member_id: Member(s) to select. None keeps all members.

    Returns:
        DataArray with member selection applied (or unchanged).
    """
    if "member_id" not in data_var.dims or member_id is None:
        return data_var

    available = set(str(v) for v in data_var.coords["member_id"].values)

    # Normalize to a list
    if not isinstance(member_id, list):
        member_id = [member_id]

    # Convert ints to the "rNi1p1f1" string format
    selected = []
    for m in member_id:
        if isinstance(m, int):
            label = f"r{m}i1p1f1"
        else:
            label = str(m)

        if label in available:
            selected.append(label)
        else:
            logger.warning("Member '%s' not found in dataset, skipping", label)

    if not selected:
        return data_var

    if len(selected) == 1:
        return data_var.sel(member_id=selected[0])
    return data_var.sel(member_id=selected)


def _make_json_serializable(obj):
    """Recursively convert objects to JSON-serializable format."""
    if isinstance(obj, list):
        return [_make_json_serializable(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _make_json_serializable(value) for key, value in obj.items()}
    if isinstance(obj, np.ndarray):
        return _make_json_serializable(obj.tolist())
    if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
        try:
            return [_make_json_serializable(item) for item in obj]
        except Exception:
            return str(obj)
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if not isinstance(obj, (str, int, float, bool, type(None))):
        return str(obj)
    return obj


def _walk_groups(zgroup, prefix: str = "", max_depth: int = 3) -> List[Dict[str, Any]]:
    """Recursively list Zarr groups and arrays from a zarr.Group."""
    items = []
    if max_depth <= 0:
        return items

    for name in sorted(zgroup.group_keys()):
        path = f"{prefix}/{name}" if prefix else name
        child = zgroup[name]
        items.append({"path": path, "type": "group"})
        items.extend(_walk_groups(child, prefix=path, max_depth=max_depth - 1))

    for name in sorted(zgroup.array_keys()):
        path = f"{prefix}/{name}" if prefix else name
        arr = zgroup[name]
        items.append({
            "path": path,
            "type": "array",
            "shape": list(arr.shape),
            "dtype": str(arr.dtype),
        })

    return items


# ── MCP tools ──────────────────────────────────────────────────────────────

def test_arraylake_connection(group: Optional[str] = None) -> Dict[str, Any]:
    """
    Test connection to the SPEAR ArrayLake repository.

    Opens the Zarr root (or a specific group if provided) and returns
    basic information about what's there.

    Args:
        group: Optional Zarr group path (e.g. "historical/Amon").
               If None, opens the repo root and lists top-level groups.

    Returns:
        Connection status, and either dataset info or root-level structure.
    """
    try:
        if group:
            ds = _open_dataset(group)
            return {
                "status": "success",
                "message": f"Connected to ArrayLake repo '{ARRAYLAKE_REPO}', group '{group}'",
                "repo": ARRAYLAKE_REPO,
                "branch": ARRAYLAKE_BRANCH,
                "group": group,
                "dimensions": dict(ds.sizes),
                "variables": list(ds.data_vars.keys()),
                "coordinates": list(ds.coords.keys()),
            }
        else:
            root = _get_root()
            groups = sorted(root.group_keys())
            arrays = sorted(root.array_keys())
            return {
                "status": "success",
                "message": f"Connected to ArrayLake repo '{ARRAYLAKE_REPO}' at root",
                "repo": ARRAYLAKE_REPO,
                "branch": ARRAYLAKE_BRANCH,
                "root_groups": groups,
                "root_arrays": arrays,
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "repo": ARRAYLAKE_REPO,
            "group": group,
        }


def browse_arraylake_repo(path: Optional[str] = None, max_depth: int = 2) -> Dict[str, Any]:
    """
    Browse the Zarr hierarchy in the SPEAR ArrayLake repository.

    Repo structure: root has 'historical' and 'scenarioSSP5-85' groups,
    each containing frequency sub-groups (Amon, day, 6hr, Omon, fx, Ofx).

    Args:
        path: Zarr group path to start from (e.g. "historical", "historical/Amon").
              If None, starts at the repo root.
        max_depth: How many levels deep to recurse (default 2, max 4).

    Returns:
        Dictionary with the tree of groups and arrays found.
    """
    try:
        max_depth = min(max_depth, 4)
        root = _get_root()
        start = root[path] if path else root

        items = _walk_groups(start, prefix=path or "", max_depth=max_depth)

        return {
            "status": "success",
            "repo": ARRAYLAKE_REPO,
            "branch": ARRAYLAKE_BRANCH,
            "start_path": path or "(root)",
            "max_depth": max_depth,
            "contents": items,
        }
    except KeyError:
        return {
            "status": "error",
            "error": f"Path '{path}' not found in repo",
            "repo": ARRAYLAKE_REPO,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_arraylake_store_info(
    group: Optional[str] = None,
    include_full_details: bool = False,
) -> Dict[str, Any]:
    """
    Get metadata from a SPEAR Zarr group on ArrayLake without loading data.

    Args:
        group: Zarr group path (e.g. "historical/Amon", "scenarioSSP5-85/day").
               If None, opens at the repo root.
        include_full_details: If True, includes coordinate values and variable
                              attributes (slower, more data transferred).

    Returns:
        Dictionary containing store metadata, dimensions, and optionally
        full coordinate/variable details.
    """
    try:
        ds = _open_dataset(group)

        metadata: Dict[str, Any] = {
            "repo": ARRAYLAKE_REPO,
            "branch": ARRAYLAKE_BRANCH,
            "group": group or "(root)",
            "data_format": "Zarr v3 (ArrayLake / Icechunk)",
            "dimensions": dict(ds.sizes),
        }

        if not include_full_details:
            metadata["variables"] = {
                name: {
                    "long_name": var.attrs.get("long_name", "N/A"),
                    "units": var.attrs.get("units", "N/A"),
                    "dimensions": list(var.dims),
                    "shape": list(var.shape),
                }
                for name, var in ds.data_vars.items()
            }
            return metadata

        # Full details
        metadata["global_attributes"] = _make_json_serializable(dict(ds.attrs))
        metadata["coordinates"] = {}
        metadata["variables"] = {}

        for coord_name, coord in ds.coords.items():
            coord_info: Dict[str, Any] = {
                "dimensions": list(coord.dims),
                "shape": list(coord.shape),
                "dtype": str(coord.dtype),
                "attributes": _make_json_serializable(dict(coord.attrs)),
            }
            if coord.size <= 1000:
                coord_info["values"] = _make_json_serializable(coord.values.tolist())
            else:
                coord_info["values_info"] = {
                    "size": int(coord.size),
                    "min": _make_json_serializable(coord.min().values),
                    "max": _make_json_serializable(coord.max().values),
                    "first_few": _make_json_serializable(coord.values[:5].tolist()),
                    "last_few": _make_json_serializable(coord.values[-5:].tolist()),
                }
            metadata["coordinates"][coord_name] = coord_info

        for var_name, var in ds.data_vars.items():
            metadata["variables"][var_name] = {
                "dimensions": list(var.dims),
                "shape": list(var.shape),
                "dtype": str(var.dtype),
                "size": int(var.size),
                "long_name": var.attrs.get("long_name", "N/A"),
                "units": var.attrs.get("units", "N/A"),
                "standard_name": var.attrs.get("standard_name", "N/A"),
                "attributes": _make_json_serializable(dict(var.attrs)),
            }

        return metadata

    except Exception as e:
        return {"error": f"Failed to get ArrayLake store metadata: {e}"}


def query_arraylake_data(
    variable: str = "tas",
    group: str = "historical/Amon",
    member_id: Optional[Union[int, str, List[int], List[str]]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    lat_range: Optional[List[float]] = None,
    lon_range: Optional[List[float]] = None,
    scenario: Optional[str] = None,
    frequency: Optional[str] = None,
    ensemble_member: Optional[str] = None,
    grid: Optional[str] = None,
    version: Optional[str] = None,
    chunk_index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Query SPEAR Zarr data on ArrayLake with spatial/temporal/ensemble subsetting.

    Data has dimensions (member_id: 30, time, [plev], lat: 360, lon: 576).
    All 30 ensemble members are in the same array.

    Args:
        variable: Variable name (e.g. "tas", "pr", "uas").
        group: Zarr group path — must include experiment AND frequency,
               e.g. "historical/Amon", "scenarioSSP5-85/day".
               Alternatively, pass scenario and frequency as separate args.
        member_id: Ensemble member(s) to select. Accepts int (1-30) or
                   string ("r1i1p1f1"). Single value or list.
                   If None, returns all 30 members (can be very large).
        start_date: Start date (e.g. "1921-01" or "1921-01-15").
        end_date: End date (e.g. "2014-12" or "2014-12-31").
        lat_range: [min_lat, max_lat] in degrees (-90 to 90).
        lon_range: [min_lon, max_lon] in degrees (-180 to 180 or 0 to 360).
        scenario: Optional — if provided without group, builds group as "scenario/frequency".
        frequency: Optional — used with scenario to build group path.
        ensemble_member: Optional — alias for member_id (e.g. "r1i1p1f1").

    Returns:
        Dictionary with queried data, coordinates, and metadata.
    """
    try:
        # Build group from scenario + frequency if provided separately
        if scenario and frequency and group == "historical/Amon":
            group = f"{scenario}/{frequency}"
        elif scenario and group == "historical/Amon":
            group = f"{scenario}/Amon"

        # Handle ensemble_member as alias for member_id
        if ensemble_member and member_id is None:
            member_id = ensemble_member

        ds = _open_dataset(group)

        if variable not in ds.data_vars:
            return {
                "error": f"Variable '{variable}' not found in group '{group}'",
                "available_variables": list(ds.data_vars.keys()),
            }

        data_var = ds[variable]

        # Ensemble member selection
        data_var = _select_members(data_var, member_id)

        # Spatial subsetting (shared utility handles coordinate conversion)
        data_var, coordinate_adjustments = subset_spatial(
            data_var, ds, lat_range, lon_range
        )

        # Temporal subsetting
        if start_date or end_date:
            time_slice = slice(
                start_date if start_date else None,
                end_date if end_date else None,
            )
            data_var = data_var.sel(time=time_slice)

        # Size guard (50 MB cap, assuming float32)
        data_size_mb = (data_var.size * 4) / (1024 * 1024)
        if data_size_mb > 50:
            return {
                "error": f"Requested data too large: {data_size_mb:.2f} MB",
                "message": "Please use smaller spatial/temporal ranges or select fewer ensemble members",
                "data_shape": list(data_var.shape),
                "data_dimensions": list(data_var.dims),
                "suggestion": "Try selecting a single member_id (1-30), a smaller time range, or a smaller spatial region",
            }

        # Trigger actual download
        data_values = data_var.values

        result: Dict[str, Any] = {
            "variable": variable,
            "repo": ARRAYLAKE_REPO,
            "group": group,
            "query_parameters": {
                "member_id": member_id,
                "start_date": start_date,
                "end_date": end_date,
                "lat_range": lat_range,
                "lon_range": lon_range,
            },
            "data_info": {
                "shape": list(data_var.shape),
                "dimensions": list(data_var.dims),
                "dtype": str(data_var.dtype),
                "size_mb": round(data_size_mb, 2),
            },
            "coordinates": {},
            "data": _make_json_serializable(data_values.tolist()),
            "attributes": _make_json_serializable(dict(data_var.attrs)),
        }

        for coord_name in data_var.coords:
            coord = data_var.coords[coord_name]
            result["coordinates"][coord_name] = {
                "values": _make_json_serializable(coord.values.tolist()),
                "attributes": _make_json_serializable(dict(coord.attrs)),
            }

        if coordinate_adjustments:
            result["coordinate_adjustments"] = coordinate_adjustments
            result["note"] = (
                "Coordinates were snapped to nearest grid points. "
                "See 'coordinate_adjustments' for details."
            )

        return result

    except Exception as e:
        return {"error": f"ArrayLake query failed: {e}"}


def get_arraylake_summary_statistics(
    variable: str = "tas",
    group: str = "historical/Amon",
    member_id: Optional[Union[int, str, List[int], List[str]]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    lat_range: Optional[List[float]] = None,
    lon_range: Optional[List[float]] = None,
    scenario: Optional[str] = None,
    frequency: Optional[str] = None,
    ensemble_member: Optional[str] = None,
    grid: Optional[str] = None,
    version: Optional[str] = None,
    chunk_index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Get summary statistics for SPEAR data on ArrayLake without returning
    full arrays.

    Args:
        variable: Variable name (e.g. "tas", "pr").
        group: Zarr group path (e.g. "historical/Amon", "scenarioSSP5-85/day").
        member_id: Ensemble member(s) to select. Accepts int (1-30) or
                   string ("r1i1p1f1"). None for all members.
        start_date: Start date.
        end_date: End date.
        lat_range: [min_lat, max_lat] in degrees.
        lon_range: [min_lon, max_lon] in degrees.
        scenario: Optional — if provided, builds group as "scenario/frequency".
        frequency: Optional — used with scenario to build group path.
        ensemble_member: Optional — alias for member_id.
        grid: Ignored (NetCDF compat).
        version: Ignored (NetCDF compat).
        chunk_index: Ignored (NetCDF compat).

    Returns:
        Dictionary with min, max, mean, std statistics.
    """
    try:
        # Build group from scenario + frequency if provided separately
        if scenario and frequency and group == "historical/Amon":
            group = f"{scenario}/{frequency}"
        elif scenario and group == "historical/Amon":
            group = f"{scenario}/Amon"

        # Handle ensemble_member as alias for member_id
        if ensemble_member and member_id is None:
            member_id = ensemble_member

        ds = _open_dataset(group)

        if variable not in ds.data_vars:
            return {"error": f"Variable '{variable}' not found in group '{group}'"}

        data_var = ds[variable]

        # Ensemble member selection
        data_var = _select_members(data_var, member_id)

        # Spatial subsetting
        data_var, _ = subset_spatial(data_var, ds, lat_range, lon_range)

        # Temporal subsetting
        if start_date or end_date:
            time_slice = slice(
                start_date if start_date else None,
                end_date if end_date else None,
            )
            data_var = data_var.sel(time=time_slice)

        return {
            "variable": variable,
            "repo": ARRAYLAKE_REPO,
            "group": group,
            "query_parameters": {
                "member_id": member_id,
                "start_date": start_date,
                "end_date": end_date,
                "lat_range": lat_range,
                "lon_range": lon_range,
            },
            "shape": list(data_var.shape),
            "dimensions": list(data_var.dims),
            "data_size_mb": round((data_var.size * 4) / (1024 * 1024), 2),
            "statistics": {
                "min": float(data_var.min().values),
                "max": float(data_var.max().values),
                "mean": float(data_var.mean().values),
                "std": float(data_var.std().values),
            },
        }

    except Exception as e:
        return {"error": f"ArrayLake statistics calculation failed: {e}"}
