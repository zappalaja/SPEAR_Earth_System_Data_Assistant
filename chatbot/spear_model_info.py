"""
SPEAR Model Information
=======================
This file contains detailed information about SPEAR climate models, their
configurations, scenarios, and technical specifications.

Modify this file to update model descriptions and capabilities.
"""

# ============================================================================
# SPEAR MODEL OVERVIEW
# ============================================================================

SPEAR_OVERVIEW = {
    "full_name": "Seamless system for Prediction and EArth system Research",
    "developer": "NOAA Geophysical Fluid Dynamics Laboratory (GFDL)",
    "purpose": "Unified climate modeling system for seasonal-to-decadal prediction and centennial climate projections",
    "key_features": [
        "Seamless prediction from weeks to centuries",
        "Large ensemble capability for uncertainty quantification",
        "High-resolution atmospheric and oceanic components",
        "Comprehensive Earth system representation"
    ],
    "documentation_url": "https://www.gfdl.noaa.gov/spear/",
    "data_location": "AWS S3 (NOAA Open Data Program)"
}

# ============================================================================
# MODEL COMPONENTS
# ============================================================================

MODEL_COMPONENTS = {
    "atmosphere": {
        "component": "AM4",
        "resolution": "~100 km horizontal (C96 grid)",
        "vertical_levels": "33 levels",
        "top_level": "~1 hPa",
        "description": "GFDL Atmospheric Model version 4 with comprehensive physics"
    },

    "ocean": {
        "component": "MOM6",
        "resolution": "~1° horizontal (0.25° in tropics)",
        "vertical_levels": "75 levels",
        "description": "Modular Ocean Model version 6 with eddy parameterization"
    },

    "sea_ice": {
        "component": "SIS2",
        "description": "Sea Ice Simulator version 2 with multiple ice thickness categories"
    },

    "land": {
        "component": "LM4",
        "description": "GFDL Land Model version 4 with carbon and nitrogen cycles"
    }
}

# ============================================================================
# SPEAR VARIANTS
# ============================================================================

SPEAR_VARIANTS = {
    "SPEAR_MED": {
        "name": "SPEAR Medium Resolution",
        "description": "Standard SPEAR configuration used for most experiments",
        "atmosphere_resolution": "~100 km (C96)",
        "ocean_resolution": "~1° (0.25° tropical)",
        "primary_use": "Climate projections and seasonal-to-decadal prediction",
        "ensemble_size": "Up to 30 members for some experiments",
        "notes": "This is the version available in the SPEAR MCP server"
    },

    "SPEAR_LO": {
        "name": "SPEAR Low Resolution",
        "description": "Lower resolution version for large ensembles",
        "atmosphere_resolution": "~200 km (C48)",
        "ocean_resolution": "~1°",
        "primary_use": "Large ensemble experiments (100+ members)",
        "notes": "Faster to run, enabling larger ensembles"
    },

    "SPEAR_HI": {
        "name": "SPEAR High Resolution",
        "description": "Higher resolution for extreme events",
        "atmosphere_resolution": "~50 km (C192)",
        "ocean_resolution": "~0.25°",
        "primary_use": "Tropical cyclones and regional climate",
        "notes": "Better representation of mesoscale features"
    }
}

# ============================================================================
# AVAILABLE SCENARIOS
# ============================================================================

SCENARIOS = {
    "historical": {
        "name": "Historical",
        "time_period": "1850-2014 (some extend to 2020)",
        "description": "Simulation using observed historical forcing",
        "forcing_agents": [
            "Observed greenhouse gas concentrations",
            "Historical aerosol emissions",
            "Solar variability",
            "Volcanic eruptions",
            "Land use changes"
        ],
        "purpose": "Validate model against observations and provide baseline for future scenarios",
        "ensemble_members": "Multiple realizations (r1i1p1f1, r2i1p1f1, etc.)",
        "notes": "Essential for understanding model performance and calculating future changes"
    },

    "scenarioSSP5-85": {
        "name": "SSP5-8.5 (High Emissions)",
        "full_name": "Shared Socioeconomic Pathway 5, RCP 8.5",
        "time_period": "2015-2100",
        "description": "High emissions scenario with fossil-fueled development",
        "radiative_forcing": "~8.5 W/m² by 2100",
        "CO2_concentration": "~1135 ppm by 2100",
        "temperature_change": "~4-5°C global mean warming by 2100 (multi-model mean)",
        "socioeconomic_narrative": "High economic growth, fossil fuel intensive, high energy demand",
        "purpose": "Upper bound of emissions scenarios, useful for risk assessment",
        "ensemble_members": "Multiple realizations available",
        "notes": "Not a prediction, but a 'what-if' scenario for high emissions pathway"
    },

    "scenarioSSP2-45": {
        "name": "SSP2-4.5 (Middle-of-the-Road)",
        "full_name": "Shared Socioeconomic Pathway 2, RCP 4.5",
        "time_period": "2015-2100",
        "description": "Intermediate emissions scenario",
        "radiative_forcing": "~4.5 W/m² by 2100",
        "CO2_concentration": "~600 ppm by 2100",
        "temperature_change": "~2-3°C global mean warming by 2100",
        "socioeconomic_narrative": "Medium challenges to mitigation and adaptation",
        "purpose": "Middle-range scenario for planning",
        "notes": "May be available in some SPEAR datasets"
    },

    "scenarioSSP1-26": {
        "name": "SSP1-2.6 (Low Emissions)",
        "full_name": "Shared Socioeconomic Pathway 1, RCP 2.6",
        "time_period": "2015-2100",
        "description": "Low emissions scenario consistent with Paris Agreement goals",
        "radiative_forcing": "~2.6 W/m² by 2100",
        "CO2_concentration": "~450 ppm by 2100",
        "temperature_change": "~1.5-2°C global mean warming by 2100",
        "socioeconomic_narrative": "Sustainable development, low energy demand",
        "purpose": "Lower bound scenario, ambitious mitigation",
        "notes": "Availability in SPEAR datasets may vary"
    }
}

# ============================================================================
# ENSEMBLE MEMBER NAMING CONVENTION
# ============================================================================

ENSEMBLE_NAMING = {
    "format": "rXiYpZfW",
    "components": {
        "r": {
            "name": "Realization",
            "description": "Different initial conditions or internal variability",
            "example": "r1, r2, r3... represent different ensemble members",
            "typical_range": "1-30 depending on experiment"
        },
        "i": {
            "name": "Initialization",
            "description": "Different initialization methods",
            "example": "i1 (most common)",
            "typical_values": "Usually i1 for SPEAR"
        },
        "p": {
            "name": "Physics",
            "description": "Different physics parameterizations",
            "example": "p1 (standard physics)",
            "typical_values": "Usually p1 for SPEAR"
        },
        "f": {
            "name": "Forcing",
            "description": "Different forcing datasets",
            "example": "f1 (standard forcing)",
            "typical_values": "Usually f1 for SPEAR"
        }
    },
    "common_examples": {
        "r1i1p1f1": "First ensemble member with standard configuration",
        "r15i1p1f1": "15th ensemble member (different initial conditions)",
        "r30i1p1f1": "30th ensemble member"
    },
    "usage_notes": "Different 'r' values represent natural climate variability. Averaging across multiple members reduces noise and reveals forced signal."
}

# ============================================================================
# DATA FREQUENCIES
# ============================================================================

DATA_FREQUENCIES = {
    "Amon": {
        "name": "Monthly Atmospheric",
        "description": "Monthly mean atmospheric variables",
        "typical_variables": ["tas", "pr", "psl", "hurs"],
        "temporal_resolution": "1 month",
        "use_cases": ["climate trends", "seasonal cycles", "long-term analysis"]
    },

    "day": {
        "name": "Daily",
        "description": "Daily mean or daily aggregate values",
        "typical_variables": ["tasmax", "tasmin", "pr"],
        "temporal_resolution": "1 day",
        "use_cases": ["extreme events", "weather patterns", "daily variability"]
    },

    "Omon": {
        "name": "Monthly Ocean",
        "description": "Monthly mean ocean variables",
        "typical_variables": ["tos", "sos", "zos"],
        "temporal_resolution": "1 month",
        "use_cases": ["ocean heat content", "sea surface temperature trends"]
    },

    "6hrLev": {
        "name": "6-Hourly Atmospheric Levels",
        "description": "6-hourly atmospheric data on pressure levels",
        "temporal_resolution": "6 hours",
        "use_cases": ["weather systems", "storms", "short-term variability"],
        "notes": "High temporal resolution, large data volumes"
    },

    "3hr": {
        "name": "3-Hourly",
        "description": "3-hourly surface variables",
        "temporal_resolution": "3 hours",
        "use_cases": ["diurnal cycles", "sub-daily variability"]
    }
}

# ============================================================================
# GRID SPECIFICATIONS
# ============================================================================

GRID_TYPES = {
    "gr3": {
        "name": "GFDL Regridded Grid 3",
        "description": "Standard regridded lat-lon grid",
        "typical_resolution": "~100 km",
        "grid_structure": "Regular latitude-longitude",
        "notes": "Most commonly used grid for SPEAR output"
    },

    "gn": {
        "name": "Native Grid",
        "description": "Model's native computational grid",
        "grid_structure": "Cubed-sphere for atmosphere, tripolar for ocean",
        "notes": "Preserves original model resolution but more complex to use"
    }
}

# ============================================================================
# MODEL STRENGTHS AND LIMITATIONS
# ============================================================================

MODEL_CAPABILITIES = {
    "strengths": [
        "Large ensemble sizes for robust uncertainty quantification",
        "Seamless predictions from seasonal to centennial timescales",
        "Well-validated against historical observations",
        "Comprehensive representation of Earth system processes",
        "Active development and continuous improvement by GFDL team"
    ],

    "limitations": [
        "~100 km resolution limits representation of small-scale features",
        "Some parameterized processes (clouds, convection) have uncertainties",
        "Ocean eddies are parameterized rather than explicitly resolved (in SPEAR_MED)",
        "Regional biases exist, particularly in precipitation patterns",
        "Single model - multi-model ensembles provide more robust projections"
    ],

    "best_use_cases": [
        "Large-scale climate patterns and trends",
        "Ensemble-based uncertainty quantification",
        "Seasonal to decadal prediction",
        "Climate change impact studies",
        "Extreme event statistics (with sufficient ensemble size)"
    ],

    "cautions": [
        "Should not be used alone for high-stakes decisions - use multi-model ensembles",
        "Local-scale projections have high uncertainty",
        "Some variables have larger uncertainties than others (e.g., precipitation vs temperature)",
        "Model performance varies by region and variable"
    ]
}

# ============================================================================
# VERSION INFORMATION
# ============================================================================

DATA_VERSIONS = {
    "v20210201": {
        "date": "February 1, 2021",
        "description": "Standard SPEAR data version",
        "notes": "Most commonly available version"
    },
    "v20190826": {
        "date": "August 26, 2019",
        "description": "Earlier SPEAR data version",
        "notes": "May be available for some variables"
    }
}

# ============================================================================
# TECHNICAL SPECIFICATIONS
# ============================================================================

TECHNICAL_SPECS = {
    "file_format": "NetCDF-4",
    "compression": "Data is compressed for efficient storage",
    "metadata_standard": "CF (Climate and Forecast) conventions",
    "calendar": "noleap (365-day calendar) or standard Gregorian",
    "data_storage": "AWS S3 (s3://noaa-gfdl-spear-*)",
    "access_methods": ["Direct S3 access", "MCP server (this interface)", "GFDL data portal"]
}

# ============================================================================
# RELATED PROJECTS AND COMPARISONS
# ============================================================================

RELATED_MODELS = {
    "CMIP6": {
        "relationship": "SPEAR contributed to CMIP6 (Coupled Model Intercomparison Project Phase 6)",
        "differences": "CMIP6 includes many models; SPEAR is GFDL's contribution",
        "complementarity": "SPEAR large ensembles complement CMIP6 multi-model ensembles"
    },

    "CESM": {
        "name": "Community Earth System Model (NCAR)",
        "comparison": "Similar purpose, different modeling center",
        "note": "Use multiple models for robust conclusions"
    },

    "GFDL-CM4": {
        "relationship": "SPEAR builds on GFDL-CM4 components",
        "differences": "SPEAR optimized for prediction and large ensembles"
    }
}
