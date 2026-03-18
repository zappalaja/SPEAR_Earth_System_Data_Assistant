"""
Variable Definitions and Climate Terminology
=============================================
This file contains official definitions, units, and descriptions for all climate
variables available in SPEAR, plus general climate science terminology.

Modify this file to customize how variables are described and explained.
"""

# ============================================================================
# SPEAR CLIMATE VARIABLES
# ============================================================================

# Atmospheric Variables
ATMOSPHERIC_VARIABLES = {
    "tas": {
        "name": "Near-Surface Air Temperature",
        "standard_name": "air_temperature",
        "units": "K (Kelvin) or °C (Celsius)",
        "description": "Temperature of air at 2 meters above the surface",
        "typical_range": "220-320 K (-53 to 47°C)",
        "interpretation": "Daily mean, monthly mean, or other temporal averaging of 2-meter air temperature",
        "use_cases": ["heat waves", "temperature trends", "climate change impacts"],
        "related_variables": ["tasmax", "tasmin"]
    },

    "tasmax": {
        "name": "Daily Maximum Near-Surface Air Temperature",
        "standard_name": "air_temperature",
        "units": "K or °C",
        "description": "Maximum temperature of air at 2 meters above surface during a day",
        "interpretation": "Useful for studying extreme heat events",
        "use_cases": ["heat wave analysis", "extreme temperature events"],
        "related_variables": ["tas", "tasmin"]
    },

    "tasmin": {
        "name": "Daily Minimum Near-Surface Air Temperature",
        "standard_name": "air_temperature",
        "units": "K or °C",
        "description": "Minimum temperature of air at 2 meters above surface during a day",
        "interpretation": "Useful for studying cold extremes and frost events",
        "use_cases": ["freeze events", "minimum temperature trends"],
        "related_variables": ["tas", "tasmax"]
    },

    "pr": {
        "name": "Precipitation",
        "standard_name": "precipitation_flux",
        "units": "kg m-2 s-1 (or mm/day when converted)",
        "description": "Total precipitation (rain + snow) rate",
        "typical_range": "0-0.001 kg m-2 s-1 (0-86 mm/day)",
        "interpretation": "Includes both liquid and solid precipitation. To convert to mm/day, multiply by 86400",
        "use_cases": ["drought analysis", "flood risk", "water resources"],
        "related_variables": ["prsn", "evspsbl"]
    },

    "prsn": {
        "name": "Snowfall Flux",
        "standard_name": "snowfall_flux",
        "units": "kg m-2 s-1",
        "description": "Precipitation that falls as snow",
        "interpretation": "Subset of total precipitation (pr)",
        "use_cases": ["winter precipitation", "snowpack analysis"],
        "related_variables": ["pr"]
    },

    "hurs": {
        "name": "Near-Surface Relative Humidity",
        "standard_name": "relative_humidity",
        "units": "% (percent)",
        "description": "Relative humidity at 2 meters above the surface",
        "typical_range": "0-100%",
        "interpretation": "Ratio of actual water vapor to saturation water vapor",
        "use_cases": ["drought monitoring", "human comfort indices", "fire weather"],
        "related_variables": ["huss"]
    },

    "huss": {
        "name": "Near-Surface Specific Humidity",
        "standard_name": "specific_humidity",
        "units": "kg/kg (mass fraction)",
        "description": "Mass of water vapor per unit mass of air at 2 meters",
        "interpretation": "Absolute measure of atmospheric moisture",
        "use_cases": ["moisture transport", "atmospheric water content"],
        "related_variables": ["hurs"]
    },

    "psl": {
        "name": "Sea Level Pressure",
        "standard_name": "air_pressure_at_mean_sea_level",
        "units": "Pa (Pascals)",
        "description": "Atmospheric pressure reduced to mean sea level",
        "typical_range": "95000-105000 Pa (950-1050 hPa)",
        "interpretation": "Used to identify weather systems (high/low pressure)",
        "use_cases": ["storm tracking", "weather patterns", "atmospheric circulation"],
        "related_variables": ["ps"]
    },

    "ps": {
        "name": "Surface Air Pressure",
        "standard_name": "surface_air_pressure",
        "units": "Pa",
        "description": "Atmospheric pressure at the surface",
        "interpretation": "Actual pressure at surface, varies with elevation",
        "use_cases": ["surface weather analysis"],
        "related_variables": ["psl"]
    },

    "uas": {
        "name": "Eastward Near-Surface Wind",
        "standard_name": "eastward_wind",
        "units": "m s-1 (meters per second)",
        "description": "Component of wind in the eastward direction at 10 meters",
        "interpretation": "Positive values indicate eastward wind, negative indicates westward",
        "use_cases": ["wind energy", "storm analysis", "atmospheric circulation"],
        "related_variables": ["vas", "sfcWind"]
    },

    "vas": {
        "name": "Northward Near-Surface Wind",
        "standard_name": "northward_wind",
        "units": "m s-1",
        "description": "Component of wind in the northward direction at 10 meters",
        "interpretation": "Positive values indicate northward wind, negative indicates southward",
        "use_cases": ["wind energy", "storm analysis", "atmospheric circulation"],
        "related_variables": ["uas", "sfcWind"]
    },

    "sfcWind": {
        "name": "Near-Surface Wind Speed",
        "standard_name": "wind_speed",
        "units": "m s-1",
        "description": "Wind speed at 10 meters above surface",
        "typical_range": "0-50 m/s (0-180 km/h)",
        "interpretation": "Magnitude of wind vector, calculated from uas and vas",
        "use_cases": ["wind energy potential", "extreme wind events"],
        "related_variables": ["uas", "vas"]
    },

    "clt": {
        "name": "Total Cloud Cover Percentage",
        "standard_name": "cloud_area_fraction",
        "units": "% (percent)",
        "description": "Percentage of sky covered by clouds",
        "typical_range": "0-100%",
        "interpretation": "Total cloud fraction in atmospheric column",
        "use_cases": ["solar energy", "radiation budget", "weather patterns"],
        "related_variables": ["rsds", "rsus"]
    }
}

# Ocean Variables
OCEAN_VARIABLES = {
    "tos": {
        "name": "Sea Surface Temperature",
        "standard_name": "sea_surface_temperature",
        "units": "K or °C",
        "description": "Temperature of ocean surface water",
        "typical_range": "271-305 K (-2 to 32°C)",
        "interpretation": "Foundation for ocean-atmosphere interaction and marine ecosystems",
        "use_cases": ["marine heat waves", "coral bleaching", "hurricane intensity"],
        "related_variables": ["sos"]
    },

    "sos": {
        "name": "Sea Surface Salinity",
        "standard_name": "sea_surface_salinity",
        "units": "psu (practical salinity units) or g/kg",
        "description": "Salt content of ocean surface water",
        "typical_range": "30-40 psu",
        "interpretation": "Indicator of ocean circulation and freshwater input",
        "use_cases": ["ocean circulation", "freshwater cycle"],
        "related_variables": ["tos"]
    },

    "zos": {
        "name": "Sea Surface Height Above Geoid",
        "standard_name": "sea_surface_height_above_geoid",
        "units": "m (meters)",
        "description": "Height of ocean surface relative to geoid",
        "interpretation": "Related to ocean circulation, thermal expansion, and sea level rise",
        "use_cases": ["sea level rise", "ocean circulation"],
        "related_variables": []
    }
}

# Radiation Variables
RADIATION_VARIABLES = {
    "rsds": {
        "name": "Surface Downwelling Shortwave Radiation",
        "standard_name": "surface_downwelling_shortwave_flux_in_air",
        "units": "W m-2 (Watts per square meter)",
        "description": "Solar radiation reaching Earth's surface",
        "interpretation": "Important for solar energy and surface energy budget",
        "use_cases": ["solar energy potential", "surface temperature"],
        "related_variables": ["rsus", "rlds"]
    },

    "rsus": {
        "name": "Surface Upwelling Shortwave Radiation",
        "standard_name": "surface_upwelling_shortwave_flux_in_air",
        "units": "W m-2",
        "description": "Solar radiation reflected from Earth's surface",
        "interpretation": "Depends on surface albedo (reflectivity)",
        "use_cases": ["surface albedo", "energy balance"],
        "related_variables": ["rsds"]
    },

    "rlds": {
        "name": "Surface Downwelling Longwave Radiation",
        "standard_name": "surface_downwelling_longwave_flux_in_air",
        "units": "W m-2",
        "description": "Thermal (infrared) radiation from atmosphere to surface",
        "interpretation": "Important component of greenhouse effect",
        "use_cases": ["greenhouse effect", "surface energy balance"],
        "related_variables": ["rlus", "rsds"]
    },

    "rlus": {
        "name": "Surface Upwelling Longwave Radiation",
        "standard_name": "surface_upwelling_longwave_flux_in_air",
        "units": "W m-2",
        "description": "Thermal radiation emitted by Earth's surface",
        "interpretation": "Function of surface temperature",
        "use_cases": ["surface temperature", "energy balance"],
        "related_variables": ["rlds"]
    }
}

# All variables combined
ALL_VARIABLES = {
    **ATMOSPHERIC_VARIABLES,
    **OCEAN_VARIABLES,
    **RADIATION_VARIABLES
}

# ============================================================================
# DIMENSION AND COORDINATE DEFINITIONS
# ============================================================================

DIMENSIONS = {
    "time": {
        "description": "Time coordinate",
        "typical_format": "Days since 1850-01-01 or YYYY-MM-DD",
        "notes": "Can be daily, monthly, or other temporal resolution"
    },

    "lat": {
        "name": "Latitude",
        "units": "degrees_north",
        "range": "-90 to 90",
        "description": "North-south position on Earth's surface",
        "notes": "Negative values are Southern Hemisphere, positive are Northern"
    },

    "lon": {
        "name": "Longitude",
        "units": "degrees_east",
        "range": "0 to 360 or -180 to 180",
        "description": "East-west position on Earth's surface",
        "notes": "SPEAR typically uses 0-360 convention"
    },

    "plev": {
        "name": "Pressure Level",
        "units": "Pa (Pascals) or hPa (hectopascals)",
        "description": "Atmospheric pressure levels",
        "typical_values": "100000, 85000, 70000, 50000, 25000, 10000 Pa",
        "notes": "Higher pressures are closer to surface"
    },

    "lev": {
        "name": "Model Level",
        "description": "Vertical model levels",
        "notes": "Native vertical coordinate of the model"
    }
}

# ============================================================================
# CLIMATE SCIENCE TERMINOLOGY
# ============================================================================

CLIMATE_TERMS = {
    "anomaly": {
        "definition": "Deviation from a reference value (usually a long-term mean)",
        "example": "A temperature anomaly of +2°C means 2°C warmer than the baseline period",
        "usage": "Often used to remove seasonal cycles and show trends"
    },

    "climatology": {
        "definition": "Long-term average of a climate variable over a reference period",
        "example": "1981-2010 climatology is the 30-year average from 1981 to 2010",
        "usage": "Baseline for calculating anomalies"
    },

    "ensemble_member": {
        "definition": "Individual model simulation with slightly different initial conditions",
        "example": "r1i1p1f1, r2i1p1f1, etc. are different ensemble members",
        "usage": "Multiple members quantify natural variability and uncertainty",
        "format": "rXiYpZfW where X=realization, Y=initialization, Z=physics, W=forcing"
    },

    "scenario": {
        "definition": "Pathway of future greenhouse gas emissions and land use",
        "examples": {
            "historical": "Observed historical climate forcing (typically 1850-2014)",
            "SSP5-8.5": "High emissions scenario, ~8.5 W/m² radiative forcing by 2100"
        },
        "usage": "Not predictions, but 'what-if' explorations of possible futures"
    },

    "forcing": {
        "definition": "External factor that changes Earth's energy balance",
        "examples": ["greenhouse gases", "solar radiation", "volcanic aerosols"],
        "units": "W/m² (Watts per square meter)"
    },

    "feedback": {
        "definition": "Process that amplifies (positive) or dampens (negative) climate change",
        "examples": {
            "positive": "Ice-albedo feedback (less ice → less reflection → more warming)",
            "negative": "Blackbody radiation (warmer Earth radiates more heat to space)"
        }
    },

    "radiative_forcing": {
        "definition": "Change in net radiation at top of atmosphere due to a forcing agent",
        "units": "W/m²",
        "interpretation": "Positive forcing warms, negative forcing cools"
    }
}

# ============================================================================
# UNIT CONVERSIONS
# ============================================================================

UNIT_CONVERSIONS = {
    "temperature": {
        "K_to_C": "°C = K - 273.15",
        "C_to_F": "°F = (°C × 9/5) + 32",
        "K_to_F": "°F = (K - 273.15) × 9/5 + 32"
    },

    "precipitation": {
        "kg_m2_s1_to_mm_day": "mm/day = kg m⁻² s⁻¹ × 86400",
        "mm_day_to_inches_day": "inches/day = mm/day × 0.0394"
    },

    "pressure": {
        "Pa_to_hPa": "hPa = Pa / 100",
        "hPa_to_mb": "mb = hPa (equivalent)"
    },

    "wind": {
        "m_s_to_km_h": "km/h = m/s × 3.6",
        "m_s_to_mph": "mph = m/s × 2.237",
        "m_s_to_knots": "knots = m/s × 1.944"
    }
}

# ============================================================================
# COMMON ACRONYMS
# ============================================================================

ACRONYMS = {
    "SPEAR": "Seamless system for Prediction and EArth system Research",
    "GFDL": "Geophysical Fluid Dynamics Laboratory",
    "NOAA": "National Oceanic and Atmospheric Administration",
    "SSP": "Shared Socioeconomic Pathway",
    "CMIP": "Coupled Model Intercomparison Project",
    "IPCC": "Intergovernmental Panel on Climate Change",
    "NetCDF": "Network Common Data Form (file format)",
    "TPM": "Tokens Per Minute (API rate limiting)",
    "RPM": "Requests Per Minute (API rate limiting)"
}
