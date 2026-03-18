"""
Confidence Assessment System
=============================

## What This Does

This module enables the chatbot to provide transparent confidence ratings for every response,
helping users understand how reliable the information is and whether additional verification
is needed.

## How Confidence is Calculated

The chatbot evaluates its confidence across **4 key dimensions** and provides both individual
category ratings and an overall confidence score:

### 1. Data Accuracy (0-100%)
**What it measures:** How confident the chatbot is that the data values are correct and from
actual SPEAR files rather than general knowledge or fabricated.

**High confidence (95-99%) when:**
- Data retrieved directly from MCP tools (query_netcdf_data, browse_spear_directory, etc.)
- Tool execution was successful with no errors
- Complete metadata is available (coordinates, time period, scenario, ensemble member)
- Data values fall within expected/documented ranges
- All spatial and temporal bounds are clearly specified

**Low confidence (0-40%) when:**
- Tool execution failed or returned errors
- Data is from the chatbot's general training knowledge, not from actual SPEAR queries
- Metadata is missing or incomplete
- Had to estimate, approximate, or infer values
- Cannot verify data against actual SPEAR files

**Example:** If you ask "What was the temperature in New York in January 2020?" and the
chatbot successfully queries SPEAR with the query_netcdf_data tool and returns data with
full metadata → Data Accuracy = 99%. But if the tool fails and the chatbot provides a
general answer → Data Accuracy = 30%.

### 2. Scientific Explanation (0-100%)
**What it measures:** How confident the chatbot is in the scientific accuracy and validity
of its explanations about climate processes, phenomena, and interpretations.

**High confidence (95-99%) when:**
- Explanation based on well-established, fundamental physics (e.g., thermodynamics)
- Supported by definitions in the knowledge base (variable_definitions.py, spear_model_info.py)
- Clear physical mechanisms with strong evidence base
- Topic is core climate science (temperature, greenhouse effect, etc.)

**Low confidence (0-40%) when:**
- Topic is outside core climate science expertise
- Limited information available in knowledge base
- Emerging research area with uncertain consensus
- Requires highly specialized domain knowledge not in the configuration files
- Involves complex regional processes with high uncertainty

**Example:** Explaining the greenhouse effect → 95% (well-established physics). Explaining
specific cloud microphysics in a particular storm → 50% (complex, uncertain processes).

### 3. Model Information (0-100%)
**What it measures:** How confident the chatbot is in details about SPEAR models, their
capabilities, configurations, and technical specifications.

**High confidence (95-99%) when:**
- Information comes directly from spear_model_info.py configuration file
- Standard, well-documented SPEAR features and configurations
- Official model specifications (resolution, components, scenarios)
- Ensemble naming conventions defined in knowledge base

**Low confidence (0-40%) when:**
- Information not documented in knowledge base files
- Specific technical details that aren't in spear_model_info.py
- Edge cases, unusual configurations, or experimental features
- Had to infer from general CMIP6/climate model knowledge
- Details about ongoing development or unreleased versions

**Example:** Describing SPEAR_MED resolution and components → 95% (in spear_model_info.py).
Discussing unpublished SPEAR experiments → 30% (not documented).

### 4. Variable Definitions (0-100%)
**What it measures:** How confident the chatbot is in variable names, units, descriptions,
and interpretations.

**High confidence (95-99%) when:**
- Variable is fully defined in variable_definitions.py
- CF (Climate and Forecast) standard name is documented
- Units, typical ranges, and use cases are specified
- Related variables and interpretation guidance available

**Low confidence (0-40%) when:**
- Variable not in variable_definitions.py knowledge base
- Unusual, derived, or custom variable
- Uncertain about units, conventions, or typical ranges
- Had to extrapolate from similar variables
- Variable naming doesn't follow standard conventions

**Example:** Defining 'tas' (near-surface air temperature) → 95% (fully documented in
variable_definitions.py). Defining an obscure derived variable → 40% (not in knowledge base).

## Overall Confidence Calculation

The **overall confidence** is calculated as a weighted average of the four categories:

**When data is presented (data query responses):**
- Data Accuracy: 40% weight (most important - is the data real?)
- Scientific Explanation: 30% weight
- Model Information: 20% weight
- Variable Definitions: 10% weight

**When only providing explanations (no data query):**
- Scientific Explanation: 50% weight (most important)
- Model Information: 30% weight
- Variable Definitions: 20% weight
- Data Accuracy: N/A (not applicable)

**Rounding:** All percentages are rounded to the nearest 5% for simplicity.

**Overall Confidence = (Category1 × Weight1) + (Category2 × Weight2) + ... **

## Confidence Levels and Visual Indicators

| Level | Range | Emoji | Meaning | User Action |
|-------|-------|-------|---------|-------------|
| **Very High** | 95-99% | 🟢 | Information directly from tools/knowledge base, well-established science | Can be used with high trust |
| **High** | 80-94% | 🟢 | Strong evidence, minor uncertainties or assumptions | Generally reliable, minor verification recommended |
| **Moderate** | 60-79% | 🟡 | Some uncertainties, reasonable assumptions made | Cross-check with other sources |
| **Low** | 40-59% | 🟠 | Significant uncertainties, important assumptions | Should verify independently |
| **Very Low** | 0-39% | 🔴 | High uncertainty, speculative or general knowledge only | Do not rely on; seek authoritative sources |

## What Affects Confidence

### Factors that INCREASE confidence:
✅ Data directly from SPEAR MCP tools (query_netcdf_data, etc.)
✅ Complete metadata present (coordinates, time, scenario, ensemble)
✅ Variable defined in knowledge base files
✅ Model information from official knowledge base
✅ Data values within expected ranges
✅ Historical data (more certain than future projections)
✅ Temperature data (more certain than precipitation)
✅ Global patterns (more certain than regional)

### Factors that DECREASE confidence:
⚠️ Tool execution failed or returned errors
⚠️ Variable not in knowledge base
⚠️ Question outside core SPEAR/climate expertise
⚠️ Regional or local details (higher uncertainty than global)
⚠️ Extreme events (harder to model than means)
⚠️ Precipitation (higher model uncertainty than temperature)
⚠️ Far future projections (compounding uncertainties)
⚠️ Derived/calculated values (not direct model output)
⚠️ Single model results (SPEAR alone vs. multi-model)
⚠️ Incomplete or missing metadata

## Why This Matters

**Transparency:** Users can see exactly what's certain vs. uncertain in each response.

**Trust:** Honesty about limitations builds credibility rather than undermining it.

**Decision-making:** Users can adjust how they use information based on confidence levels.

**Quality control:** Low confidence flags potential issues (tool failures, knowledge gaps).

**Education:** Helps users understand inherent uncertainties in climate science.

## Example Confidence Assessment

After a response about temperature data from SPEAR:

---
**Confidence Assessment:**

📊 **Overall Confidence: 95%** 🟢

**Breakdown:**
- 🔍 **Data Accuracy:** 99% - Data from query_netcdf_data with complete metadata
- 🧪 **Scientific Explanation:** 95% - Temperature trends are well-established
- 🖥️ **Model Information:** 95% - SPEAR scenario info from knowledge base
- 📋 **Variable Definitions:** 90% - 'tas' fully defined in variable_definitions.py

**Key Factors:**
- ✅ All data from verified SPEAR MCP tools
- ✅ Complete spatial and temporal metadata provided
---

## Customization

You can customize confidence thresholds, weights, and criteria by editing the constants
in this file. See CONFIGURATION_GUIDE.md for examples.

"""

# ============================================================================
# CONFIDENCE CATEGORIES
# ============================================================================

CONFIDENCE_CATEGORIES = {
    "data_accuracy": {
        "name": "Data Accuracy",
        "description": "Confidence that data values are correct and from actual SPEAR files",
        "high_indicators": [
            "Data retrieved directly from MCP tools",
            "Tool execution successful",
            "Metadata matches request",
            "Values within expected ranges"
        ],
        "low_indicators": [
            "Tool execution failed",
            "Had to estimate or approximate",
            "Data from memory rather than tools",
            "Missing metadata"
        ]
    },

    "scientific_explanation": {
        "name": "Scientific Explanation",
        "description": "Confidence in scientific accuracy of explanations",
        "high_indicators": [
            "Explanation based on well-established physics",
            "Supported by knowledge base definitions",
            "Clear physical mechanisms"
        ],
        "low_indicators": [
            "Topic outside core expertise",
            "Limited information available",
            "Emerging research area",
            "Requires domain-specific knowledge not in knowledge base"
        ]
    },

    "model_information": {
        "name": "Model Information",
        "description": "Confidence in SPEAR model details and capabilities",
        "high_indicators": [
            "Information from knowledge base (spear_model_info.py)",
            "Standard SPEAR configurations",
            "Well-documented features"
        ],
        "low_indicators": [
            "Information not in knowledge base",
            "Specific technical details not documented",
            "Edge cases or unusual configurations"
        ]
    },

    "variable_definitions": {
        "name": "Variable Definitions",
        "description": "Confidence in variable descriptions and units",
        "high_indicators": [
            "Variable defined in knowledge base",
            "CF standard name available",
            "Clear units and typical ranges"
        ],
        "low_indicators": [
            "Variable not in knowledge base",
            "Unusual or derived variable",
            "Uncertain about units or conventions"
        ]
    }
}

# ============================================================================
# CONFIDENCE LEVEL DEFINITIONS
# ============================================================================

CONFIDENCE_LEVELS = {
    "very_high": {
        "range": "95-99%",
        "label": "Very High",
        "emoji": "🟢",
        "description": "Information directly from tools/knowledge base, well-established science"
    },
    "high": {
        "range": "80-94%",
        "label": "High",
        "emoji": "🟢",
        "description": "Strong evidence, minor uncertainties or assumptions"
    },
    "moderate": {
        "range": "60-79%",
        "label": "Moderate",
        "emoji": "🟡",
        "description": "Some uncertainties, reasonable assumptions made"
    },
    "low": {
        "range": "40-59%",
        "label": "Low",
        "emoji": "🟠",
        "description": "Significant uncertainties, important assumptions"
    },
    "very_low": {
        "range": "0-39%",
        "label": "Very Low",
        "emoji": "🔴",
        "description": "High uncertainty, speculative or general knowledge only"
    }
}

# ============================================================================
# ASSESSMENT INSTRUCTIONS FOR AI
# ============================================================================

CONFIDENCE_ASSESSMENT_INSTRUCTIONS = """

## CONFIDENCE SELF-ASSESSMENT

After every response, you MUST provide a confidence assessment in the following format:

---
**Confidence Assessment:**

📊 **Overall Confidence: [X]%** [emoji]

**Breakdown:**
- 🔍 **Data Accuracy:** [X]% - [Brief justification]
- 🧪 **Scientific Explanation:** [X]% - [Brief justification]
- 🖥️ **Model Information:** [X]% - [Brief justification]
- 📋 **Variable Definitions:** [X]% - [Brief justification] (if applicable)

**Key Factors:**
- ✅ [What increases confidence]
- ⚠️ [What decreases confidence, if any]

---

### Guidelines for Each Category:

**Data Accuracy (0-100%):**
- 95-99%: Data directly from successful tool execution, all metadata present
- 80-94%: Data from tools but minor gaps (e.g., partial metadata)
- 60-79%: Some data from tools, some from knowledge base/memory
- 40-59%: Mostly from memory/knowledge base, minimal tool verification
- 0-39%: No tool verification, general knowledge only or tool errors

**Scientific Explanation (0-100%):**
- 95-99%: Well-established physics, matches knowledge base
- 80-94%: Strong scientific basis, minor simplifications
- 60-79%: Generally accepted, some assumptions or simplifications
- 40-59%: Basic principles, significant uncertainties
- 0-39%: Outside core expertise, highly uncertain

**Model Information (0-100%):**
- 95-99%: Directly from knowledge base configuration files
- 80-94%: From knowledge base with minor inference
- 60-79%: Partial knowledge base info, some general CMIP6 knowledge
- 40-59%: General climate model knowledge, not SPEAR-specific
- 0-39%: Speculative or uncertain

**Variable Definitions (0-100%):**
- 95-99%: Variable fully defined in knowledge base
- 80-94%: Variable in knowledge base, minor details inferred
- 60-79%: Similar variable in knowledge base, extrapolated
- 40-59%: General climate knowledge, not in knowledge base
- 0-39%: Unfamiliar variable, uncertain definition

### When to Flag Low Confidence:

ALWAYS clearly indicate when confidence is moderate or below:
- Tool execution failed → Low data accuracy
- Question outside SPEAR scope → Lower overall confidence
- Variable not in knowledge base → Lower variable definition confidence
- Emerging science topic → Lower scientific explanation confidence

### Overall Confidence Calculation:

Calculate overall confidence as weighted average:
- If data was presented: Data Accuracy (40%), Scientific (30%), Model (20%), Variables (10%)
- If explanation only: Scientific (50%), Model (30%), Variables (20%)
- Round to nearest 5%

### Examples:

**Example 1: High Confidence Response**
```
---
**Confidence Assessment:**

📊 **Overall Confidence: 95%** 🟢

**Breakdown:**
- 🔍 **Data Accuracy:** 99% - Data retrieved directly from query_netcdf_data tool with complete metadata
- 🧪 **Scientific Explanation:** 95% - Temperature trends are well-established climate science
- 🖥️ **Model Information:** 95% - SPEAR scenario information from knowledge base
- 📋 **Variable Definitions:** 90% - 'tas' fully defined in variable_definitions.py

**Key Factors:**
- ✅ All data from verified SPEAR MCP tools
- ✅ Complete metadata provided (coordinates, time, scenario, ensemble)
---
```

**Example 2: Moderate Confidence Response**
```
---
**Confidence Assessment:**

📊 **Overall Confidence: 70%** 🟡

**Breakdown:**
- 🔍 **Data Accuracy:** 85% - Data from tools but limited spatial coverage
- 🧪 **Scientific Explanation:** 65% - Regional climate patterns have higher uncertainty
- 🖥️ **Model Information:** 75% - Some SPEAR-specific details inferred
- 📋 **Variable Definitions:** 55% - Derived variable not directly in knowledge base

**Key Factors:**
- ✅ Core data from SPEAR tools
- ⚠️ Regional projections have higher uncertainty than global
- ⚠️ Derived variable definition based on component variables
---
```

**Example 3: Low Confidence Response**
```
---
**Confidence Assessment:**

📊 **Overall Confidence: 45%** 🟠

**Breakdown:**
- 🔍 **Data Accuracy:** 30% - Tool execution failed, providing general information only
- 🧪 **Scientific Explanation:** 60% - General climate science, not SPEAR-specific
- 🖥️ **Model Information:** 40% - Limited information in knowledge base for this aspect
- 📋 **Variable Definitions:** 50% - Variable not in knowledge base, using general knowledge

**Key Factors:**
- ⚠️ Could not retrieve SPEAR data due to tool error
- ⚠️ Response based on general climate knowledge, not verified against SPEAR
- ⚠️ User should verify information with direct data access
- ✅ Scientific principles are sound, but SPEAR-specific details uncertain
---
```

## IMPORTANT RULES:

1. **Always include confidence assessment** - Every response must have one
2. **Be honest** - Don't inflate confidence when uncertain
3. **Be specific** - Explain what increases/decreases confidence
4. **Use the format** - Follow the template above exactly
5. **Round to 5%** - Use multiples of 5 for all percentages
6. **Match emoji to level** - 🟢 (80-99%), 🟡 (60-79%), 🟠 (40-59%), 🔴 (0-39%)
7. **Adjust for context** - If user asks a question you can't answer with tools, be explicit about lower confidence
8. **Tool failures = lower confidence** - If tools fail, overall confidence should reflect that

"""

# ============================================================================
# HELPER FUNCTIONS FOR CONFIDENCE PHRASES
# ============================================================================

CONFIDENCE_PHRASES = {
    "very_high": [
        "I'm very confident in this information",
        "This is well-established and verified",
        "High confidence based on direct data access",
        "This information is directly from SPEAR tools and knowledge base"
    ],
    "high": [
        "I'm confident in this information",
        "This is well-supported by the data",
        "Strong confidence with minor uncertainties",
        "This is based on verified SPEAR data"
    ],
    "moderate": [
        "I'm moderately confident in this information",
        "This has reasonable support but some uncertainties",
        "Moderate confidence - some assumptions made",
        "This is likely correct but has some limitations"
    ],
    "low": [
        "I have limited confidence in this",
        "This should be verified with additional sources",
        "Low confidence - significant uncertainties",
        "This is based on general knowledge rather than SPEAR-specific data"
    ],
    "very_low": [
        "I have very limited confidence in this",
        "This is highly uncertain and should be independently verified",
        "Very low confidence - outside my expertise",
        "This is speculative and may not be accurate"
    ]
}

# ============================================================================
# FACTORS THAT INCREASE/DECREASE CONFIDENCE
# ============================================================================

CONFIDENCE_FACTORS = {
    "increases_confidence": [
        "✅ Data retrieved directly from SPEAR MCP tools",
        "✅ All metadata present (coordinates, time, scenario, ensemble)",
        "✅ Variable defined in knowledge base",
        "✅ Model information from official knowledge base",
        "✅ Data values within expected ranges",
        "✅ Multiple ensemble members confirm pattern",
        "✅ Results consistent with physical understanding",
        "✅ Clear documentation in configuration files"
    ],

    "decreases_confidence": [
        "⚠️ Tool execution failed or returned errors",
        "⚠️ Variable not in knowledge base",
        "⚠️ Question outside core SPEAR expertise",
        "⚠️ Regional details (higher uncertainty than global)",
        "⚠️ Extreme events (higher uncertainty)",
        "⚠️ Precipitation (higher model uncertainty than temperature)",
        "⚠️ Far future projections (compounding uncertainties)",
        "⚠️ Derived or calculated values (not direct model output)",
        "⚠️ Single model (SPEAR alone, not multi-model)",
        "⚠️ Incomplete metadata",
        "⚠️ Edge cases or unusual configurations"
    ]
}
