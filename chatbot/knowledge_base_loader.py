"""
Knowledge Base Loader
=====================
This module loads configuration files and formats them into sections for the AI system prompt.
Centralizes all knowledge base content for easy maintenance and updates.
"""

from chat_regulation import *
from variable_definitions import *
from spear_model_info import *
from confidence_assessment import CONFIDENCE_ASSESSMENT_INSTRUCTIONS
from document_processor import build_documents_prompt
from spear_data_paths import (
    QUICK_REFERENCE, DIRECT_ACCESS_GUIDE, SCENARIOS as DATA_SCENARIOS,
    VARIABLES, VARIABLE_ALIASES, ENSEMBLE_MEMBERS, FREQUENCIES,
    REGIONS, CITIES, TIME_RANGES, DEFAULT_GRID, DEFAULT_VERSION
)


def build_knowledge_base_prompt():
    """
    Build comprehensive knowledge base text to append to system prompt.
    Returns formatted string with all configuration information.
    """

    prompt = "\n\n" + "=" * 80 + "\n"
    prompt += "KNOWLEDGE BASE - SPEAR DATA AND TERMINOLOGY\n"
    prompt += "=" * 80 + "\n\n"

    # ========================================================================
    # PRECOMPUTED DATA PATHS - DIRECT ACCESS (NO BROWSING NEEDED!)
    # ========================================================================
    prompt += "## PRECOMPUTED DATA PATHS - SKIP BROWSING, ACCESS DATA DIRECTLY!\n\n"
    prompt += "**CRITICAL: You already know ALL available paths. DO NOT browse directories.**\n"
    prompt += "**When a user asks for data, go DIRECTLY to query_netcdf_data with these known values:**\n\n"

    prompt += QUICK_REFERENCE + "\n\n"

    prompt += "### SINGLE POINT vs REGION:\n"
    prompt += "- **Single point** (city): use lat_range=[lat, lat], lon_range=[lon, lon]\n"
    prompt += "- **Region** (country/area): use lat_range=[min, max], lon_range=[min, max]\n\n"

    prompt += "### PRECOMPUTED CITIES (single points):\n"
    for city_key, city_data in list(CITIES.items())[:10]:
        name = city_data.get('name', city_key.replace('_', ' ').title())
        prompt += f"- **{name}**: lat={city_data['lat']}, lon={city_data['lon']}\n"

    prompt += "\n### PRECOMPUTED REGIONS (lat_range, lon_range):\n"
    for region_key, region_data in list(REGIONS.items())[:12]:
        name = region_data.get('name', region_key.replace('_', ' ').title())
        prompt += f"- **{name}**: lat={region_data['lat_range']}, lon={region_data['lon_range']}\n"

    prompt += "\n### VARIABLE ALIASES (what users say -> variable name):\n"
    for alias, var in list(VARIABLE_ALIASES.items())[:15]:
        prompt += f"- \"{alias}\" -> `{var}`\n"

    prompt += "\n### DIRECT ACCESS EXAMPLES:\n"
    prompt += """
**User: "Show me temperature for the US"**
-> IMMEDIATELY call query_netcdf_data with:
   - variable="tas", scenario="historical", ensemble_member="r1i1p1f1"
   - frequency="Amon", grid="gr3", version="v20210201"
   - lat_range=[24, 50], lon_range=[235, 295] (CONUS coordinates)
   - start_date="2010-01", end_date="2014-12" (reasonable recent range)

**User: "What will precipitation be like in Mexico in 2050?"**
-> IMMEDIATELY call query_netcdf_data with:
   - variable="pr", scenario="scenarioSSP5-85", ensemble_member="r1i1p1f1"
   - frequency="Amon", grid="gr3", version="v20210201"
   - lat_range=[14, 33], lon_range=[242, 274] (Mexico coordinates)
   - start_date="2045-01", end_date="2055-12"

**DO NOT** call browse_spear_directory first - you already know the structure!
"""

    prompt += "\n" + "=" * 80 + "\n\n"

    # ========================================================================
    # CONTROLLED VOCABULARY SECTION
    # ========================================================================
    prompt += "## RESPONSE GUIDELINES AND CONTROLLED VOCABULARY\n\n"

    prompt += "### Topics to Avoid:\n"
    for topic in PROHIBITED_TOPICS:
        prompt += f"- {topic}\n"

    prompt += "\n### Sensitive Topics Requiring Caution:\n"
    for topic in SENSITIVE_TOPICS:
        prompt += f"- {topic}\n"

    prompt += "\n### Preferred Terminology:\n"
    for wrong, right in list(PREFERRED_TERMS.items())[:5]:  # Show first 5 examples
        prompt += f"- Use '{right}' instead of '{wrong}'\n"

    prompt += "\n### Phrases to Avoid:\n"
    for phrase in AVOID_PHRASES[:6]:  # Show first 6
        prompt += f"- Avoid: '{phrase}'\n"

    prompt += "\n### Communicating Uncertainty:\n"
    prompt += "Use these standard terms when expressing confidence:\n"
    for level, probability in list(CONFIDENCE_LEVELS.items())[:4]:
        prompt += f"- {level.replace('_', ' ').title()}: {probability}\n"

    # ========================================================================
    # VARIABLE DEFINITIONS SECTION
    # ========================================================================
    prompt += "\n\n## SPEAR CLIMATE VARIABLES\n\n"

    prompt += "### Key Atmospheric Variables:\n"
    key_atmos = ["tas", "pr", "psl", "hurs", "sfcWind"]
    for var in key_atmos:
        if var in ALL_VARIABLES:
            info = ALL_VARIABLES[var]
            prompt += f"\n**{var}** - {info['name']}\n"
            prompt += f"  - Units: {info['units']}\n"
            prompt += f"  - Description: {info['description']}\n"

    prompt += "\n### Key Ocean Variables:\n"
    for var, info in OCEAN_VARIABLES.items():
        prompt += f"\n**{var}** - {info['name']}\n"
        prompt += f"  - Units: {info['units']}\n"
        prompt += f"  - Description: {info['description']}\n"

    prompt += "\n### Important Climate Terms:\n"
    for term in ["anomaly", "ensemble_member", "scenario", "forcing"]:
        if term in CLIMATE_TERMS:
            info = CLIMATE_TERMS[term]
            prompt += f"\n**{term}**: {info['definition']}\n"

    prompt += "\n### Common Acronyms:\n"
    for acronym, expansion in list(ACRONYMS.items())[:6]:
        prompt += f"- **{acronym}**: {expansion}\n"

    # ========================================================================
    # SPEAR MODEL INFORMATION SECTION
    # ========================================================================
    prompt += "\n\n## SPEAR MODEL INFORMATION\n\n"

    prompt += f"**Full Name:** {SPEAR_OVERVIEW['full_name']}\n"
    prompt += f"**Developer:** {SPEAR_OVERVIEW['developer']}\n"
    prompt += f"**Purpose:** {SPEAR_OVERVIEW['purpose']}\n\n"

    prompt += "### SPEAR_MED (Medium Resolution - Available in this interface):\n"
    med_info = SPEAR_VARIANTS['SPEAR_MED']
    prompt += f"- Atmosphere: {med_info['atmosphere_resolution']}\n"
    prompt += f"- Ocean: {med_info['ocean_resolution']}\n"
    prompt += f"- Primary Use: {med_info['primary_use']}\n"

    prompt += "\n### Available Scenarios:\n\n"

    prompt += "**historical** (1850-2014):\n"
    hist = SCENARIOS['historical']
    prompt += f"- {hist['description']}\n"
    prompt += f"- Purpose: {hist['purpose']}\n"

    prompt += "\n**scenarioSSP5-85** (2015-2100):\n"
    ssp585 = SCENARIOS['scenarioSSP5-85']
    prompt += f"- {ssp585['description']}\n"
    prompt += f"- Radiative Forcing: {ssp585['radiative_forcing']}\n"
    prompt += f"- Expected Warming: {ssp585['temperature_change']}\n"
    prompt += f"- {ssp585['notes']}\n"

    prompt += "\n### **CRITICAL: Automatic Scenario Selection Based on Year**\n"
    prompt += "You MUST select the correct scenario based on the user's requested time period:\n"
    prompt += "- **Years before 2015** (e.g., 1990, 2000, 2010) → use `scenario='historical'`\n"
    prompt += "- **Years 2015 or later** (e.g., 2020, 2030, 2050, 2080) → use `scenario='scenarioSSP5-85'`\n"
    prompt += "- **Spans across 2015** (e.g., 2010-2020) → use `scenario='scenarioSSP5-85'` for the future portion\n"
    prompt += "- **NEVER ask the user which scenario** - infer it automatically from the year!\n\n"

    prompt += "### **CRITICAL: Frequency Availability and Performance**\n"
    prompt += "Not all frequencies are suitable for this interface:\n"
    prompt += "- **Amon (monthly)**: RECOMMENDED - Fast, available for full range (1921-2100)\n"
    prompt += "- **day (daily)**: Available but slower, use only for short time ranges (1-2 years max)\n"
    prompt += "- **6hr (6-hourly)**: **NOT RECOMMENDED** - Files are extremely large and will likely timeout!\n"
    prompt += "  - If user asks for 6hr data, WARN them it will be very slow or fail\n"
    prompt += "  - Suggest using monthly (Amon) data instead for reliable results\n"
    prompt += "  - Only attempt 6hr if user insists, and use very small time/space ranges\n\n"

    prompt += "\n### Ensemble Member Naming (rXiYpZfW):\n"
    for component, info in ENSEMBLE_NAMING['components'].items():
        prompt += f"- **{component}**: {info['description']}\n"

    prompt += "\n### Data Frequencies:\n"
    for freq in ["Amon", "day", "Omon"]:
        if freq in DATA_FREQUENCIES:
            info = DATA_FREQUENCIES[freq]
            prompt += f"- **{freq}**: {info['description']} ({info['temporal_resolution']})\n"

    # ========================================================================
    # MODEL CAPABILITIES AND LIMITATIONS
    # ========================================================================
    prompt += "\n\n## SPEAR MODEL STRENGTHS AND LIMITATIONS\n\n"

    prompt += "### Strengths:\n"
    for strength in MODEL_CAPABILITIES['strengths'][:4]:
        prompt += f"- {strength}\n"

    prompt += "\n### Limitations (Always Acknowledge):\n"
    for limitation in MODEL_CAPABILITIES['limitations'][:4]:
        prompt += f"- {limitation}\n"

    prompt += "\n### Cautions When Using SPEAR Data:\n"
    for caution in MODEL_CAPABILITIES['cautions'][:3]:
        prompt += f"- {caution}\n"

    # ========================================================================
    # DATA ATTRIBUTION
    # ========================================================================
    prompt += "\n\n## DATA ATTRIBUTION REQUIREMENTS\n\n"
    prompt += f"- Always cite: {ATTRIBUTION_REQUIREMENTS['data_source']}\n"
    prompt += f"- {ATTRIBUTION_REQUIREMENTS['model_reference']}\n"
    prompt += f"- {ATTRIBUTION_REQUIREMENTS['uncertainty']}\n"

    # ========================================================================
    # REFERENCE DOCUMENTS
    # ========================================================================
    prompt += build_documents_prompt()

    # ========================================================================
    # RESPONSE SIZE MANAGEMENT
    # ========================================================================
    prompt += "\n\n" + "=" * 80 + "\n"
    prompt += "RESPONSE SIZE MANAGEMENT\n"
    prompt += "=" * 80 + "\n\n"
    prompt += "**CRITICAL**: Before querying large datasets, estimate response size to avoid token limit errors.\n\n"
    prompt += "**Token Limits:**\n"
    prompt += "- Maximum: 200,000 tokens per request\n"
    prompt += "- Safe threshold: ~100,000 tokens (conservative limit accounting for conversation + response)\n"
    prompt += "- Typical conversation: ~15,000-30,000 tokens\n"
    prompt += "- Note: Size checker is intentionally conservative to prevent errors\n\n"
    prompt += "**Size Estimation Guidelines:**\n\n"
    prompt += "When a user requests data, estimate the size:\n"
    prompt += "- Small query (OK): 1 year monthly, regional (10°×10°) = ~10,000 tokens\n"
    prompt += "- Medium query (OK): 5 years monthly, regional (20°×20°) = ~50,000 tokens\n"
    prompt += "- Large query (WARNING): 20+ years monthly, large region = ~200,000+ tokens\n"
    prompt += "- Very large query (TOO BIG): 80 years monthly, global = ~5,000,000+ tokens\n\n"
    prompt += "**Geographic Coordinate System:**\n\n"
    prompt += "**NOTE**: SPEAR uses 0-360 longitude format\n"
    prompt += "- **Latitude**: -90 to 90 degrees (standard)\n"
    prompt += "- **Longitude**: 0 to 360 degrees\n\n"
    prompt += "**Automatic longitude conversion:**\n"
    prompt += "- You can use standard -180/180 format - it will be automatically converted!\n"
    prompt += "- Examples (conversion happens automatically):\n"
    prompt += "  - Americas: -140 to -50 → auto-converts to 220 to 310\n"
    prompt += "  - Europe: -10 to 40 → auto-converts to 350 to 40\n"
    prompt += "  - Asia: 70 to 150 → no conversion needed\n\n"
    prompt += "**Rules for Large Queries:**\n\n"
    prompt += "1. If time × lat × lon > ~100,000 data points, it's likely too large\n"
    prompt += "2. Global data (180×360 grid) for 80 years monthly = 5+ million tokens (TOO BIG)\n"
    prompt += "3. The query_netcdf_data tool has AUTOMATIC size and coordinate validation built-in\n"
    prompt += "4. If a query is too large or has invalid coordinates, the tool will return an error\n"
    prompt += "5. **CRITICAL**: When you receive an error, DO NOT retry the same tool\n"
    prompt += "6. Instead, acknowledge the issue and present the alternatives/corrections to the user\n"
    prompt += "7. Wait for the user to provide a corrected query\n\n"
    prompt += "**What to do when query is too large:**\n\n"
    prompt += "Instead of running the tool and getting an error, proactively respond:\n\n"
    prompt += "---\n"
    prompt += "## Response Too Large\n\n"
    prompt += "This query would generate too much data for our conversation (estimated: X million tokens).\n\n"
    prompt += "### Suggested Alternatives:\n\n"
    prompt += "**1. Reduce time range**\n"
    prompt += "   - Request fewer years (e.g., 2020-2030 instead of 2015-2100)\n"
    prompt += "   - Example: 'Show me temperature for 2020-2030'\n\n"
    prompt += "**2. Reduce spatial coverage**\n"
    prompt += "   - Focus on specific region instead of global\n"
    prompt += "   - Example: 'Show me data for the Northeast US (40-45°N, 70-75°W)'\n\n"
    prompt += "**3. Request spatial average**\n"
    prompt += "   - Get area-averaged values instead of full grid\n"
    prompt += "   - Example: 'What is the average temperature over this region?'\n\n"
    prompt += "**4. Use Python code for large data**\n"
    prompt += "   - Provide example code to access data directly:\n\n"
    prompt += "```python\n"
    prompt += "import xarray as xr\n"
    prompt += "# Open SPEAR dataset\n"
    prompt += "ds = xr.open_dataset('s3://noaa-gfdl-spear-...')\n"
    prompt += "# Select and process data\n"
    prompt += "data = ds['variable'].sel(time=slice(...), lat=slice(...), lon=slice(...))\n"
    prompt += "result = data.mean(dim=['lat', 'lon'])  # Spatial average\n"
    prompt += "```\n"
    prompt += "---\n\n"
    prompt += "**Examples of queries you should warn about:**\n"
    prompt += "- 'Show me global temperature for 2015-2100' → TOO BIG (suggest region or shorter time)\n"
    prompt += "- 'Plot precipitation for all ensemble members globally' → TOO BIG (suggest one member or region)\n"
    prompt += "- 'Give me daily data for 50 years' → TOO BIG (suggest monthly or shorter period)\n\n"

    # ========================================================================
    # CONFIDENCE ASSESSMENT INSTRUCTIONS
    # ========================================================================
    prompt += CONFIDENCE_ASSESSMENT_INSTRUCTIONS

    prompt += "\n" + "=" * 80 + "\n"
    prompt += "END OF KNOWLEDGE BASE\n"
    prompt += "=" * 80 + "\n"

    return prompt
