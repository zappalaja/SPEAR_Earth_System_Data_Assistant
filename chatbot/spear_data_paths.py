"""
SPEAR Data Paths - Precomputed Reference for Direct Data Access
================================================================
This file contains ALL precomputed paths, variables, and metadata for the SPEAR
climate data portal. The chatbot should use this reference to DIRECTLY access
data without needing to browse directories.

IMPORTANT: When a user asks for climate data, use these precomputed paths to
construct the correct tool call parameters IMMEDIATELY - do NOT browse directories.
"""

# ============================================================================
# BASE CONFIGURATION
# ============================================================================

SPEAR_BASE_URL = "https://noaa-gfdl-spear-large-ensembles-pds.s3.amazonaws.com"
SPEAR_BASE_PATH = "SPEAR/GFDL-LARGE-ENSEMBLES/CMIP/NOAA-GFDL/GFDL-SPEAR-MED"

# Standard grid and version (these are ALWAYS the same)
DEFAULT_GRID = "gr3"
DEFAULT_VERSION = "v20210201"

# ============================================================================
# SCENARIOS - The two available climate scenarios
# ============================================================================

SCENARIOS = {
    "historical": {
        "name": "Historical",
        "time_period": "1921-2014",
        "description": "Simulation using observed historical climate forcing",
        "data_start_year": 1921,
        "data_end_year": 2014,
        "path": "historical",
        "notes": "Validate model against observations; baseline for future changes"
    },
    "scenarioSSP5-85": {
        "name": "SSP5-8.5 (High Emissions)",
        "time_period": "2015-2100",
        "description": "High emissions scenario with fossil-fueled development",
        "data_start_year": 2015,
        "data_end_year": 2100,
        "path": "scenarioSSP5-85",
        "radiative_forcing": "~8.5 W/m2 by 2100",
        "expected_warming": "~4-5C global mean warming by 2100",
        "notes": "Upper bound emissions scenario for risk assessment"
    }
}

# Short aliases for scenarios (what users might say)
SCENARIO_ALIASES = {
    "historical": "historical",
    "hist": "historical",
    "past": "historical",
    "ssp585": "scenarioSSP5-85",
    "ssp5-85": "scenarioSSP5-85",
    "ssp5": "scenarioSSP5-85",
    "future": "scenarioSSP5-85",
    "projection": "scenarioSSP5-85",
    "high emissions": "scenarioSSP5-85",
    "rcp85": "scenarioSSP5-85"
}

# ============================================================================
# ENSEMBLE MEMBERS - 30 members available for both scenarios
# ============================================================================

# All 30 ensemble members (r1i1p1f1 through r30i1p1f1)
ENSEMBLE_MEMBERS = [f"r{i}i1p1f1" for i in range(1, 31)]

# Explanation of naming convention
ENSEMBLE_NAMING = {
    "format": "rXi1p1f1",
    "r": "Realization number (1-30) - different initial conditions for natural variability",
    "i": "Initialization method (always 1)",
    "p": "Physics configuration (always 1)",
    "f": "Forcing dataset (always 1)",
    "usage": "Use multiple ensemble members to quantify uncertainty from natural variability"
}

# ============================================================================
# FREQUENCIES - Time resolution of data
# ============================================================================

FREQUENCIES = {
    "Amon": {
        "name": "Monthly Atmospheric",
        "description": "Monthly mean atmospheric variables",
        "temporal_resolution": "1 month",
        "best_for": ["climate trends", "seasonal analysis", "long-term changes"],
        "data_points_per_year": 12
    },
    "day": {
        "name": "Daily",
        "description": "Daily mean or daily aggregate values",
        "temporal_resolution": "1 day",
        "best_for": ["extreme events", "weather patterns", "heat waves", "cold spells"],
        "data_points_per_year": 365
    },
    "6hr": {
        "name": "6-Hourly",
        "description": "6-hourly data (high temporal resolution)",
        "temporal_resolution": "6 hours",
        "best_for": ["storms", "diurnal cycles", "rapid changes"],
        "data_points_per_year": 1460,
        "warning": "Large data volumes - use smaller spatial/temporal ranges"
    },
    "Omon": {
        "name": "Monthly Ocean",
        "description": "Monthly mean ocean variables",
        "temporal_resolution": "1 month",
        "best_for": ["ocean temperature trends", "marine heat waves"]
    },
    "fx": {
        "name": "Fixed (Atmosphere)",
        "description": "Time-invariant atmospheric fields",
        "best_for": ["grid cell areas", "land-sea masks", "topography"]
    },
    "Ofx": {
        "name": "Fixed (Ocean)",
        "description": "Time-invariant ocean fields",
        "best_for": ["ocean grid areas", "bathymetry"]
    }
}

# ============================================================================
# VARIABLES BY FREQUENCY - Complete list of all available variables
# ============================================================================

VARIABLES = {
    "Amon": {
        # Most commonly requested variables
        "tas": {
            "name": "Near-Surface Air Temperature",
            "units": "K (Kelvin)",
            "conversion": "Celsius = K - 273.15",
            "description": "Temperature at 2m above surface",
            "use_cases": ["climate change", "heat waves", "temperature trends"]
        },
        "pr": {
            "name": "Precipitation",
            "units": "kg m-2 s-1",
            "conversion": "mm/day = value * 86400",
            "description": "Total precipitation rate (rain + snow)",
            "use_cases": ["drought", "floods", "water resources"]
        },
        "psl": {
            "name": "Sea Level Pressure",
            "units": "Pa",
            "conversion": "hPa = Pa / 100",
            "description": "Atmospheric pressure at sea level",
            "use_cases": ["storm tracking", "weather patterns"]
        },
        "sfcWind": {
            "name": "Near-Surface Wind Speed",
            "units": "m s-1",
            "description": "Wind speed at 10m above surface",
            "use_cases": ["wind energy", "extreme winds"]
        },
        # Atmospheric dynamics
        "hus": {
            "name": "Specific Humidity",
            "units": "kg/kg",
            "description": "Mass of water vapor per unit mass of air",
            "use_cases": ["moisture transport", "humidity trends"]
        },
        "ta": {
            "name": "Air Temperature (3D)",
            "units": "K",
            "description": "Temperature at various pressure levels",
            "use_cases": ["atmospheric profile", "upper-air analysis"]
        },
        "ua": {
            "name": "Eastward Wind (3D)",
            "units": "m s-1",
            "description": "Wind in eastward direction at pressure levels",
            "use_cases": ["jet stream", "circulation patterns"]
        },
        "va": {
            "name": "Northward Wind (3D)",
            "units": "m s-1",
            "description": "Wind in northward direction at pressure levels",
            "use_cases": ["meridional circulation"]
        },
        "uas": {
            "name": "Eastward Near-Surface Wind",
            "units": "m s-1",
            "description": "Surface wind in eastward direction"
        },
        "vas": {
            "name": "Northward Near-Surface Wind",
            "units": "m s-1",
            "description": "Surface wind in northward direction"
        },
        "zg": {
            "name": "Geopotential Height",
            "units": "m",
            "description": "Height of pressure surfaces",
            "use_cases": ["weather patterns", "blocking events"]
        },
        # Radiation variables
        "rlut": {
            "name": "Outgoing Longwave Radiation",
            "units": "W m-2",
            "description": "Thermal radiation leaving top of atmosphere",
            "use_cases": ["energy balance", "greenhouse effect"]
        },
        "rsdt": {
            "name": "Incoming Shortwave Radiation",
            "units": "W m-2",
            "description": "Solar radiation at top of atmosphere"
        },
        "rsut": {
            "name": "Outgoing Shortwave Radiation",
            "units": "W m-2",
            "description": "Reflected solar radiation at top of atmosphere"
        }
    },

    "day": {
        "tas": {
            "name": "Daily Mean Near-Surface Air Temperature",
            "units": "K",
            "description": "Daily average temperature at 2m"
        },
        "tasmax": {
            "name": "Daily Maximum Temperature",
            "units": "K",
            "description": "Maximum temperature during the day",
            "use_cases": ["heat waves", "extreme heat events"]
        },
        "tasmin": {
            "name": "Daily Minimum Temperature",
            "units": "K",
            "description": "Minimum temperature during the day",
            "use_cases": ["frost events", "cold spells"]
        },
        "pr": {
            "name": "Daily Precipitation",
            "units": "kg m-2 s-1",
            "description": "Daily total precipitation rate",
            "use_cases": ["extreme rainfall", "drought"]
        },
        "psl": {
            "name": "Daily Sea Level Pressure",
            "units": "Pa",
            "description": "Daily mean sea level pressure"
        },
        "uas": {
            "name": "Daily Eastward Near-Surface Wind",
            "units": "m s-1"
        },
        "vas": {
            "name": "Daily Northward Near-Surface Wind",
            "units": "m s-1"
        }
    },

    "6hr": {
        "pr": {
            "name": "6-Hourly Precipitation",
            "units": "kg m-2 s-1",
            "description": "Precipitation at 6-hour intervals",
            "warning": "Very large data volume"
        }
    },

    "Omon": {
        "tos": {
            "name": "Sea Surface Temperature",
            "units": "K",
            "conversion": "Celsius = K - 273.15",
            "description": "Temperature of ocean surface",
            "use_cases": ["marine heat waves", "coral bleaching", "hurricane intensity"]
        }
    },

    "fx": {
        "areacella": {
            "name": "Grid Cell Area",
            "units": "m2",
            "description": "Area of each atmospheric grid cell",
            "use_cases": ["spatial averaging", "area weighting"]
        }
    }
}

# Variable aliases (what users might say -> actual variable name)
VARIABLE_ALIASES = {
    # Temperature
    "temperature": "tas",
    "temp": "tas",
    "surface temperature": "tas",
    "air temperature": "tas",
    "t2m": "tas",
    "2m temperature": "tas",
    "max temperature": "tasmax",
    "maximum temperature": "tasmax",
    "min temperature": "tasmin",
    "minimum temperature": "tasmin",
    "daily max": "tasmax",
    "daily min": "tasmin",

    # Precipitation
    "precipitation": "pr",
    "precip": "pr",
    "rainfall": "pr",
    "rain": "pr",

    # Pressure
    "pressure": "psl",
    "sea level pressure": "psl",
    "slp": "psl",
    "mslp": "psl",

    # Wind
    "wind": "sfcWind",
    "wind speed": "sfcWind",
    "surface wind": "sfcWind",
    "u wind": "uas",
    "v wind": "vas",

    # Ocean
    "sst": "tos",
    "sea surface temperature": "tos",
    "ocean temperature": "tos",

    # Humidity
    "humidity": "hus",
    "specific humidity": "hus",

    # Radiation
    "olr": "rlut",
    "outgoing longwave": "rlut"
}

# ============================================================================
# FILENAME PATTERNS - How to construct filenames
# ============================================================================

# ============================================================================
# FILE STRUCTURE - CRITICAL: Bot must know which files contain which years!
# ============================================================================
# The query_netcdf_data tool handles file selection automatically based on dates.
# This info helps the bot understand the data structure WITHOUT browsing.

FILE_STRUCTURE = {
    "Amon": {
        "description": "Monthly data - SINGLE FILE covers entire period",
        "historical": {
            "date_range": "192101-201412",
            "years": "1921-2014",
            "single_file": True
        },
        "scenarioSSP5-85": {
            "date_range": "201501-210012",
            "years": "2015-2100",
            "single_file": True
        }
    },
    "day": {
        "description": "Daily data - SPLIT INTO 10-YEAR CHUNKS",
        "historical": {
            "chunks": [
                {"years": "1921-1930", "date_range": "19210101-19301231"},
                {"years": "1931-1940", "date_range": "19310101-19401231"},
                {"years": "1941-1950", "date_range": "19410101-19501231"},
                {"years": "1951-1960", "date_range": "19510101-19601231"},
                {"years": "1961-1970", "date_range": "19610101-19701231"},
                {"years": "1971-1980", "date_range": "19710101-19801231"},
                {"years": "1981-1990", "date_range": "19810101-19901231"},
                {"years": "1991-2000", "date_range": "19910101-20001231"},
                {"years": "2001-2010", "date_range": "20010101-20101231"},
                {"years": "2011-2014", "date_range": "20110101-20141231"},
            ]
        },
        "scenarioSSP5-85": {
            "chunks": [
                {"years": "2015-2020", "date_range": "20150101-20201231"},
                {"years": "2021-2030", "date_range": "20210101-20301231"},
                {"years": "2031-2040", "date_range": "20310101-20401231"},
                {"years": "2041-2050", "date_range": "20410101-20501231"},
                {"years": "2051-2060", "date_range": "20510101-20601231"},
                {"years": "2061-2070", "date_range": "20610101-20701231"},
                {"years": "2071-2080", "date_range": "20710101-20801231"},
                {"years": "2081-2090", "date_range": "20810101-20901231"},
                {"years": "2091-2100", "date_range": "20910101-21001231"},
            ]
        }
    }
}

# Helper to find correct file chunk for a given year
def get_file_chunk_for_year(year: int, frequency: str = "day") -> dict:
    """
    Find which file chunk contains data for a given year.

    Args:
        year: The year to look up (e.g., 2028)
        frequency: "day" or "Amon"

    Returns:
        dict with 'scenario', 'date_range', and 'years' info
    """
    scenario = "historical" if year <= 2014 else "scenarioSSP5-85"

    if frequency == "Amon":
        # Monthly files cover entire period
        info = FILE_STRUCTURE["Amon"][scenario]
        return {"scenario": scenario, **info}

    elif frequency == "day":
        chunks = FILE_STRUCTURE["day"][scenario]["chunks"]
        for chunk in chunks:
            start_year, end_year = map(int, chunk["years"].split("-"))
            if start_year <= year <= end_year:
                return {"scenario": scenario, **chunk}

    return None

FILENAME_PATTERNS = {
    "Amon": "{var}_Amon_GFDL-SPEAR-MED_{scenario}_{ensemble}_{grid}_{date_range}.nc",
    "day": "{var}_day_GFDL-SPEAR-MED_{scenario}_{ensemble}_{grid}_{date_range}.nc",
    "6hr": "{var}_6hr_GFDL-SPEAR-MED_{scenario}_{ensemble}_{grid}_{date_range}.nc",
    "Omon": "{var}_Omon_GFDL-SPEAR-MED_{scenario}_{ensemble}_{grid}_{date_range}.nc",
    "fx": "{var}_fx_GFDL-SPEAR-MED_{scenario}_{ensemble}_{grid}.nc",

    "date_formats": {
        "Amon": "YYYYMM-YYYYMM (e.g., 192101-201412)",
        "day": "YYYYMMDD-YYYYMMDD (e.g., 19210101-19301231)",
        "6hr": "YYYYMMDD-YYYYMMDD"
    },

    "example_historical_Amon": "tas_Amon_GFDL-SPEAR-MED_historical_r1i1p1f1_gr3_192101-201412.nc",
    "example_historical_day": "pr_day_GFDL-SPEAR-MED_historical_r4i1p1f1_gr3_19210101-19301231.nc",
    "example_ssp585_Amon": "tas_Amon_GFDL-SPEAR-MED_scenarioSSP5-85_r1i1p1f1_gr3_201501-210012.nc"
}

# ============================================================================
# TIME RANGES - Data availability by scenario
# ============================================================================

TIME_RANGES = {
    "historical": {
        "Amon": {"start": "1921-01", "end": "2014-12", "format": "YYYY-MM"},
        "day": {
            "start": "1921-01-01",
            "end": "2014-12-31",
            "format": "YYYY-MM-DD",
            "note": "Files split into 10-year chunks (e.g., 19210101-19301231)"
        },
        "6hr": {"start": "1921-01-01", "end": "2014-12-31"}
    },
    "scenarioSSP5-85": {
        "Amon": {"start": "2015-01", "end": "2100-12", "format": "YYYY-MM"},
        "day": {"start": "2015-01-01", "end": "2100-12-31"},
        "6hr": {"start": "2015-01-01", "end": "2100-12-31"}
    }
}

# ============================================================================
# SPATIAL COVERAGE - Grid information
# ============================================================================

SPATIAL_INFO = {
    "grid": "gr3",
    "resolution": {
        "degrees": "~1 degree",
        "kilometers": "~100 km at equator",
        "note": "Data represents area averages over each grid cell, NOT point measurements"
    },
    "grid_snapping": {
        "behavior": "Requested coordinates snap to nearest grid point",
        "example": "Request 19.4°N → Data from nearest grid point (e.g., 19.5°N)",
        "important": "ALWAYS report actual grid point used to user"
    },
    "latitude": {
        "range": [-90, 90],
        "resolution": "~1 degree",
        "units": "degrees_north",
        "note": "Negative = Southern Hemisphere, Positive = Northern Hemisphere"
    },
    "longitude": {
        "range": [0, 360],
        "resolution": "~1 degree",
        "units": "degrees_east",
        "note": "Uses 0-360 convention (NOT -180 to 180)",
        "conversion": {
            "Western Hemisphere": "Add 360 to negative longitudes (e.g., -100 -> 260)",
            "examples": {
                "New York (-74W)": 286,
                "Los Angeles (-118W)": 242,
                "London (0E)": 0,
                "Tokyo (140E)": 140
            }
        }
    },
    "user_communication": {
        "before_query": "Warn user about ~1° resolution and grid snapping",
        "after_query": "Report ACTUAL grid point coordinates used",
        "context": "Explain data represents ~100km area average, not precise location"
    }
}

# ============================================================================
# CITIES/LOCATIONS - Single point coordinates (use same value for min/max)
# ============================================================================
# For single locations, use: lat_range=[lat, lat], lon_range=[lon, lon]
# The tool will snap to the nearest grid point (~1 degree resolution)

CITIES = {
    # North America
    "new_york": {"lat": 40.7, "lon": 286.0, "name": "New York City"},  # -74 + 360 = 286
    "los_angeles": {"lat": 34.1, "lon": 241.8, "name": "Los Angeles"},  # -118.2 + 360 = 241.8
    "chicago": {"lat": 41.9, "lon": 272.4, "name": "Chicago"},  # -87.6 + 360 = 272.4
    "houston": {"lat": 29.8, "lon": 264.6, "name": "Houston"},  # -95.4 + 360 = 264.6
    "miami": {"lat": 25.8, "lon": 279.8, "name": "Miami"},  # -80.2 + 360 = 279.8
    "seattle": {"lat": 47.6, "lon": 237.7, "name": "Seattle"},  # -122.3 + 360 = 237.7
    "denver": {"lat": 39.7, "lon": 255.0, "name": "Denver"},  # -105 + 360 = 255
    "mexico_city": {"lat": 19.4, "lon": 260.9, "name": "Mexico City"},  # -99.1 + 360 = 260.9
    "toronto": {"lat": 43.7, "lon": 280.6, "name": "Toronto"},  # -79.4 + 360 = 280.6

    # Europe
    "london": {"lat": 51.5, "lon": 359.9, "name": "London"},  # -0.1 + 360 = 359.9
    "paris": {"lat": 48.9, "lon": 2.3, "name": "Paris"},
    "berlin": {"lat": 52.5, "lon": 13.4, "name": "Berlin"},
    "madrid": {"lat": 40.4, "lon": 356.3, "name": "Madrid"},  # -3.7 + 360 = 356.3
    "rome": {"lat": 41.9, "lon": 12.5, "name": "Rome"},

    # Asia
    "tokyo": {"lat": 35.7, "lon": 139.7, "name": "Tokyo"},
    "beijing": {"lat": 39.9, "lon": 116.4, "name": "Beijing"},
    "shanghai": {"lat": 31.2, "lon": 121.5, "name": "Shanghai"},
    "mumbai": {"lat": 19.1, "lon": 72.9, "name": "Mumbai"},
    "singapore": {"lat": 1.3, "lon": 103.8, "name": "Singapore"},

    # Other
    "sydney": {"lat": -33.9, "lon": 151.2, "name": "Sydney"},
    "sao_paulo": {"lat": -23.5, "lon": 313.4, "name": "São Paulo"},  # -46.6 + 360 = 313.4
    "cairo": {"lat": 30.0, "lon": 31.2, "name": "Cairo"},
    "lagos": {"lat": 6.5, "lon": 3.4, "name": "Lagos"},
}

# City name aliases
CITY_ALIASES = {
    "nyc": "new_york", "new york": "new_york", "ny": "new_york",
    "la": "los_angeles", "l.a.": "los_angeles",
    "cdmx": "mexico_city", "mexico city": "mexico_city",
    "sf": "san_francisco", "san francisco": "san_francisco",
}

# Common geographic regions with precomputed coordinates (in 0-360 format)
REGIONS = {
    "global": {"lat_range": [-90, 90], "lon_range": [0, 360]},

    # North America
    "conus": {"lat_range": [24, 50], "lon_range": [235, 295], "name": "Continental US"},
    "us_northeast": {"lat_range": [37, 47], "lon_range": [280, 295], "name": "US Northeast"},
    "us_southeast": {"lat_range": [25, 37], "lon_range": [275, 295], "name": "US Southeast"},
    "us_midwest": {"lat_range": [37, 49], "lon_range": [260, 280], "name": "US Midwest"},
    "us_southwest": {"lat_range": [31, 42], "lon_range": [245, 260], "name": "US Southwest"},
    "us_west": {"lat_range": [32, 49], "lon_range": [235, 250], "name": "US West Coast"},
    "alaska": {"lat_range": [51, 72], "lon_range": [170, 230], "name": "Alaska"},
    "mexico": {"lat_range": [14, 33], "lon_range": [242, 274], "name": "Mexico"},
    "canada": {"lat_range": [42, 72], "lon_range": [230, 295], "name": "Canada"},

    # Europe
    "europe": {"lat_range": [35, 72], "lon_range": [350, 40], "name": "Europe"},
    "western_europe": {"lat_range": [36, 60], "lon_range": [350, 15], "name": "Western Europe"},
    "mediterranean": {"lat_range": [30, 46], "lon_range": [350, 40], "name": "Mediterranean"},

    # Asia
    "east_asia": {"lat_range": [20, 55], "lon_range": [100, 150], "name": "East Asia"},
    "south_asia": {"lat_range": [5, 35], "lon_range": [60, 100], "name": "South Asia"},
    "southeast_asia": {"lat_range": [-10, 25], "lon_range": [95, 140], "name": "Southeast Asia"},

    # Tropics
    "tropics": {"lat_range": [-23, 23], "lon_range": [0, 360], "name": "Tropics"},
    "enso_region": {"lat_range": [-5, 5], "lon_range": [170, 270], "name": "ENSO Region (Nino 3.4)"},

    # Other
    "arctic": {"lat_range": [66, 90], "lon_range": [0, 360], "name": "Arctic"},
    "antarctic": {"lat_range": [-90, -60], "lon_range": [0, 360], "name": "Antarctic"},
    "australia": {"lat_range": [-45, -10], "lon_range": [110, 155], "name": "Australia"},
    "amazon": {"lat_range": [-15, 5], "lon_range": [280, 320], "name": "Amazon Basin"},
    "sahel": {"lat_range": [10, 20], "lon_range": [340, 40], "name": "Sahel"},
}

# ============================================================================
# DIRECT ACCESS INSTRUCTIONS - Skip browsing, go straight to data!
# ============================================================================

DIRECT_ACCESS_GUIDE = """
## DIRECT DATA ACCESS - NO BROWSING NEEDED

When a user requests climate data, use these precomputed paths to call tools DIRECTLY.

### For query_netcdf_data:
Parameters you ALWAYS know:
- grid: "gr3" (always)
- version: "v20210201" (always)
- scenario: "historical" or "scenarioSSP5-85"
- ensemble_member: r1i1p1f1 through r30i1p1f1 (default: r1i1p1f1)
- frequency: "Amon" (monthly), "day" (daily), "6hr" (6-hourly)
- variable: Use VARIABLES dict above to map user request to variable name

### Example Direct Calls:

User: "Show me temperature for the US in 2020"
-> query_netcdf_data(
    variable="tas",
    scenario="historical",
    ensemble_member="r1i1p1f1",
    frequency="Amon",
    grid="gr3",
    version="v20210201",
    start_date="2010-01",
    end_date="2014-12",
    lat_range=[24, 50],
    lon_range=[235, 295]
)

User: "What will precipitation be like in 2050?"
-> query_netcdf_data(
    variable="pr",
    scenario="scenarioSSP5-85",
    ensemble_member="r1i1p1f1",
    frequency="Amon",
    grid="gr3",
    version="v20210201",
    start_date="2045-01",
    end_date="2055-12",
    lat_range=[user_specified],
    lon_range=[user_specified]
)

### For get_s3_file_metadata_only:
Use when user asks about file structure or available data:
-> get_s3_file_metadata_only(
    scenario="historical",
    ensemble_member="r1i1p1f1",
    frequency="Amon",
    variable="tas",
    grid="gr3",
    version="v20210201"
)
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def resolve_variable(user_input: str) -> str:
    """Convert user's variable description to actual variable name."""
    user_input_lower = user_input.lower().strip()
    if user_input_lower in VARIABLE_ALIASES:
        return VARIABLE_ALIASES[user_input_lower]
    # Check if it's already a valid variable name
    for freq_vars in VARIABLES.values():
        if user_input_lower in freq_vars:
            return user_input_lower
    return user_input  # Return as-is if not found

def resolve_scenario(user_input: str) -> str:
    """Convert user's scenario description to actual scenario name."""
    user_input_lower = user_input.lower().strip()
    if user_input_lower in SCENARIO_ALIASES:
        return SCENARIO_ALIASES[user_input_lower]
    return user_input

def infer_scenario_from_year(year: int) -> str:
    """
    Automatically determine the correct scenario based on the year.

    Args:
        year: The year requested (e.g., 2032)

    Returns:
        "historical" for 1921-2014, "scenarioSSP5-85" for 2015-2100

    Example:
        infer_scenario_from_year(2032) -> "scenarioSSP5-85"
        infer_scenario_from_year(2000) -> "historical"
    """
    if year <= 2014:
        return "historical"
    else:
        return "scenarioSSP5-85"

def get_region_coords(region_name: str) -> dict:
    """Get lat/lon coordinates for a named region."""
    region_lower = region_name.lower().replace(" ", "_").replace("-", "_")
    return REGIONS.get(region_lower, None)

def get_city_coords(city_name: str) -> dict:
    """
    Get coordinates for a city/location as a single point.

    Returns dict with 'lat' and 'lon' for single point queries.
    For query_netcdf_data, use: lat_range=[lat, lat], lon_range=[lon, lon]

    Example:
        city = get_city_coords("Mexico City")
        -> {"lat": 19.4, "lon": 260.9, "name": "Mexico City"}

        # Then use in query:
        lat_range=[city['lat'], city['lat']]
        lon_range=[city['lon'], city['lon']]
    """
    city_lower = city_name.lower().replace(" ", "_").replace("-", "_")

    # Check aliases first
    if city_lower in CITY_ALIASES:
        city_lower = CITY_ALIASES[city_lower]

    return CITIES.get(city_lower, None)

def get_location_coords(location_name: str) -> tuple:
    """
    Get coordinates for any location (city OR region).

    Returns:
        (coords_dict, location_type) where:
        - coords_dict: the coordinate data
        - location_type: "city" (single point) or "region" (range)

    Example:
        coords, loc_type = get_location_coords("Mexico City")
        -> ({"lat": 19.4, "lon": 260.9}, "city")

        coords, loc_type = get_location_coords("Mexico")
        -> ({"lat_range": [14, 33], "lon_range": [242, 274]}, "region")
    """
    # Try city first
    city = get_city_coords(location_name)
    if city:
        return city, "city"

    # Try region
    region = get_region_coords(location_name)
    if region:
        return region, "region"

    return None, None

def convert_longitude(lon: float) -> float:
    """Convert longitude from -180/180 to 0/360 format."""
    if lon < 0:
        return lon + 360
    return lon

def get_frequency_for_variable(variable: str) -> list:
    """Return which frequencies have data for a given variable."""
    available_in = []
    for freq, vars_dict in VARIABLES.items():
        if variable in vars_dict:
            available_in.append(freq)
    return available_in

def build_full_path(scenario: str, ensemble: str, frequency: str,
                    variable: str, grid: str = "gr3", version: str = "v20210201") -> str:
    """Build the complete S3 path for a SPEAR dataset."""
    return f"{SPEAR_BASE_PATH}/{scenario}/{ensemble}/{frequency}/{variable}/{grid}/{version}"

def get_url(scenario: str, ensemble: str, frequency: str,
            variable: str, grid: str = "gr3", version: str = "v20210201") -> str:
    """Build the complete URL for a SPEAR dataset."""
    path = build_full_path(scenario, ensemble, frequency, variable, grid, version)
    return f"{SPEAR_BASE_URL}/{path}"


# ============================================================================
# QUICK REFERENCE SUMMARY (for system prompt)
# ============================================================================

QUICK_REFERENCE = """
=== SPEAR DATA QUICK REFERENCE ===

🚨 NEVER USE browse_spear_directory or search_spear_variables!
🚨 ALWAYS USE query_netcdf_data DIRECTLY - it finds the correct file automatically!

FILE STRUCTURE (query_netcdf_data handles this automatically):
- Amon (monthly): Single file covers entire period
- day (daily): 10-year chunks (2015-2020, 2021-2030, 2031-2040, etc.)
- Example: 2028 data is in the 2021-2030 file - query_netcdf_data finds it!

SINGLE POINT vs REGION:
- City (single point): lat_range=[19.4, 19.4], lon_range=[260.9, 260.9] (SAME value twice!)
- Region: lat_range=[14, 33], lon_range=[242, 274] (min, max)

GRID RESOLUTION (~1 degree / ~100km):
- Data snaps to nearest grid point
- ALWAYS report actual coordinates used to user

AUTOMATIC YEAR → SCENARIO:
- Year 1921-2014 → "historical"
- Year 2015-2100 → "scenarioSSP5-85"

SCENARIOS:
- historical (1921-2014): Past climate with observed forcing
- scenarioSSP5-85 (2015-2100): High emissions future scenario

ENSEMBLE MEMBERS: r1i1p1f1 through r30i1p1f1 (30 total, use r1i1p1f1 as default)

FREQUENCIES:
- Amon: Monthly (best for trends, climate change)
- day: Daily (best for extremes, heat waves)
- 6hr: 6-hourly (high resolution, large data)
- Omon: Monthly ocean data

KEY VARIABLES:
- tas: Surface temperature (K)
- pr: Precipitation (kg m-2 s-1, multiply by 86400 for mm/day)
- psl: Sea level pressure (Pa)
- tasmax/tasmin: Daily max/min temperature
- tos: Sea surface temperature

GRID: gr3 (always), ~1 degree resolution
VERSION: v20210201 (always)

LONGITUDE FORMAT: 0-360 (convert negative: -100 -> 260)

COMMON REGIONS (lat, lon in 0-360):
- CONUS: [24,50], [235,295]
- Europe: [35,72], [350,40]
- East Asia: [20,55], [100,150]
"""
