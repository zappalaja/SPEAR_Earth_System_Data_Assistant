"""
SPEAR Earth System Data Assistant
===========================
A Streamlit-based chatbot that uses Ollama with MCP (Model Context Protocol)
tools to access and analyze SPEAR climate model data.

Features:
- Direct integration with SPEAR climate data via MCP tools
- Real-time data querying and analysis
- Conversational interface with context retention
- Tool execution with visual feedback
"""

import streamlit as st
import os
import json
import sys
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

# Load environment variables FIRST - before importing mcp_tools_wrapper
# This ensures MCP_SERVER_URL is set when the wrapper initializes
load_dotenv()

# Auth — must be imported after load_dotenv so AUTH_ENABLED is already set
from auth_setup import setup_auth, get_user_avatar, get_bot_avatar, update_user_profile, _avatar_selector, _get_avatar_files

# Import configuration and tools
from ai_config import (
    MODEL_NAME,
    MAX_TOKENS,
    TEMPERATURE,
    SYSTEM_PROMPT,
    CHAT_TITLE,
    CHAT_INPUT_PLACEHOLDER,
    WELCOME_MESSAGE,
    DEFAULT_PROVIDER,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_CLAUDE_MODEL,
    CLAUDE_MODELS,
    DEFAULT_GEMINI_MODEL,
    GEMINI_MODELS,
)
from mcp_tools_wrapper import query_mcp_tool
from ollama_tools import OLLAMA_TOOLS
from llm_provider import OllamaProvider, ClaudeProvider, GeminiProvider, get_provider, ANTHROPIC_AVAILABLE, GOOGLE_AVAILABLE

# ============================================================================
# CONFIGURATION
# ============================================================================

# Add the src directory to the system path for SPEAR MCP tools access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Initialize Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_API_FLAVOR = os.getenv("OLLAMA_API_FLAVOR", "").strip().lower()

if OLLAMA_BASE_URL.endswith("/api/chat"):
    OLLAMA_BASE_URL = OLLAMA_BASE_URL[: -len("/api/chat")]
elif OLLAMA_BASE_URL.endswith("/api/tags"):
    OLLAMA_BASE_URL = OLLAMA_BASE_URL[: -len("/api/tags")]
elif OLLAMA_BASE_URL.endswith("/v1/chat/completions"):
    OLLAMA_BASE_URL = OLLAMA_BASE_URL[: -len("/v1/chat/completions")]
elif OLLAMA_BASE_URL.endswith("/v1/models"):
    OLLAMA_BASE_URL = OLLAMA_BASE_URL[: -len("/v1/models")]

if OLLAMA_BASE_URL.endswith("/v1") or OLLAMA_API_FLAVOR == "openai":
    OLLAMA_API_MODE = "openai"
    OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/chat/completions"
    OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/models"
elif OLLAMA_BASE_URL.endswith("/api") or OLLAMA_API_FLAVOR == "native":
    OLLAMA_API_MODE = "native"
    OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/chat"
    OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/tags"
else:
    OLLAMA_API_MODE = "native"
    OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
    OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"

# ============================================================================
# UI SETUP
# ============================================================================

# Run auth gate — st.stop() is called inside if user is not authenticated
_authenticator, current_user = setup_auth()
user_avatar = get_user_avatar(current_user)  # None = Streamlit default icon
bot_avatar = get_bot_avatar()               # None = Streamlit default icon

# ── Background image ─────────────────────────────────────────────────────────
_bg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "background")
_bg_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
if os.path.isdir(_bg_dir):
    _bg_candidates = sorted(
        f for f in os.listdir(_bg_dir)
        if os.path.splitext(f)[1].lower() in _bg_exts
    )
    if _bg_candidates:
        import base64 as _base64
        _bg_path = os.path.join(_bg_dir, _bg_candidates[0])
        with open(_bg_path, "rb") as _f:
            _bg_b64 = _base64.b64encode(_f.read()).decode()
        _bg_ext = os.path.splitext(_bg_candidates[0])[1].lower().lstrip(".")
        _bg_mime = "jpeg" if _bg_ext in ("jpg", "jpeg") else _bg_ext
        st.markdown(f"""
            <style>
            /* Background + white overlay stacked directly on .stApp */
            .stApp {{
                background-image:
                    linear-gradient(rgba(255, 255, 255, 0.80), rgba(255, 255, 255, 0.80)),
                    url("data:image/{_bg_mime};base64,{_bg_b64}") !important;
                background-size: cover !important;
                background-position: center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            }}
            /* Sidebar overrides .stApp with its own dark overlay */
            [data-testid="stSidebar"] {{
                background-image:
                    linear-gradient(rgba(0, 0, 0, 0.60), rgba(0, 0, 0, 0.60)),
                    url("data:image/{_bg_mime};base64,{_bg_b64}") !important;
                background-size: cover !important;
                background-position: center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            }}
            /* Black text in main area */
            .stApp * {{
                color: black !important;
            }}
            /* Download button — white text on colored background */
            .stApp .stDownloadButton button {{
                color: white !important;
                background-color: #0068c9 !important;
                border: none !important;
            }}
            .stApp .stDownloadButton button:hover {{
                background-color: #0050a0 !important;
            }}
            .stApp .stDownloadButton button * {{
                color: white !important;
            }}
            /* Fullscreen (expand) / element toolbar buttons on plots/images */
            [data-testid="stElementToolbar"] button {{
                color: white !important;
                background-color: rgba(0, 0, 0, 0.6) !important;
                border-radius: 4px !important;
                opacity: 1 !important;
            }}
            [data-testid="stElementToolbar"] button svg,
            [data-testid="stElementToolbar"] button path {{
                color: white !important;
                fill: white !important;
                stroke: white !important;
            }}
            /* Restore warning/alert box colors — currentColor turns black without this */
            [data-testid="stAlert"] {{
                background-color: rgba(255, 220, 0, 0.35) !important;
                border-color: rgba(200, 160, 0, 0.9) !important;
            }}
            /* Inline code (tool names in backticks) — yellow highlight */
            .stApp code {{
                background-color: rgba(255, 220, 0, 0.45) !important;
                color: black !important;
                border-radius: 3px !important;
                padding: 1px 4px !important;
            }}
            /* Sidebar text white */
            [data-testid="stSidebar"] * {{
                color: white !important;
            }}
            /* Sidebar expanders — no yellow */
            [data-testid="stSidebar"] details,
            [data-testid="stSidebar"] [data-testid="stExpander"] {{
                background-color: transparent !important;
                border-left: none !important;
            }}
            /* Header bar (Deploy button area) — transparent so .stApp gradient shows through */
            [data-testid="stHeader"] {{
                background: transparent !important;
            }}
            /* Bottom bar — transparent so .stApp background shows through */
            [data-testid="stBottom"],
            [data-testid="stBottom"] > div,
            [data-testid="stBottom"] > div > div {{
                background: transparent !important;
                backdrop-filter: none !important;
                box-shadow: none !important;
            }}
            [data-testid="stBottom"]::before {{
                background: none !important;
            }}
            /* White text and arrow in chat input bar */
            [data-testid="stBottom"] *,
            [data-testid="stBottom"] textarea {{
                color: white !important;
            }}
            [data-testid="stBottom"] textarea::placeholder {{
                color: rgba(255, 255, 255, 0.6) !important;
            }}
            [data-testid="stBottom"] button svg {{
                fill: white !important;
                stroke: white !important;
            }}
            /* ── Standalone expanders (outside chat bubbles) — light background ── */
            [data-testid="stMain"] [data-testid="stExpander"] details {{
                background-color: #f8f8f8 !important;
            }}
            [data-testid="stMain"] [data-testid="stExpander"] [data-testid="stJson"],
            [data-testid="stMain"] [data-testid="stExpander"] [data-testid="stJson"] > div {{
                background-color: #f8f8f8 !important;
            }}
            [data-testid="stMain"] [data-testid="stExpander"] [data-testid="stCodeBlock"] > div,
            [data-testid="stMain"] [data-testid="stExpander"] pre {{
                background-color: #f0f0f0 !important;
                color: #333 !important;
            }}
            [data-testid="stMain"] [data-testid="stExpander"] code {{
                background-color: transparent !important;
                color: #333 !important;
            }}
            /* ── Expanders inside chat message bubbles — dark header, light content ── */
            /* Must come AFTER stMain rules to override via cascade */
            [data-testid="stChatMessage"] [data-testid="stExpander"] details {{
                background-color: transparent !important;
            }}
            [data-testid="stChatMessage"] [data-testid="stExpander"] summary,
            [data-testid="stChatMessage"] [data-testid="stExpander"] summary * {{
                color: black !important;
                background-color: transparent !important;
            }}
            /* Content area — target the JSON viewer, code blocks, and alert boxes */
            [data-testid="stChatMessage"] [data-testid="stExpander"] [data-testid="stJson"] {{
                background-color: #f8f8f8 !important;
                border-radius: 4px !important;
            }}
            [data-testid="stChatMessage"] [data-testid="stExpander"] [data-testid="stJson"] * {{
                background-color: transparent !important;
                color: #333 !important;
            }}
            [data-testid="stChatMessage"] [data-testid="stExpander"] [data-testid="stAlert"] {{
                background-color: rgba(255, 220, 0, 0.35) !important;
            }}
            [data-testid="stChatMessage"] [data-testid="stExpander"] [data-testid="stAlert"] * {{
                color: #333 !important;
            }}
            [data-testid="stChatMessage"] [data-testid="stExpander"] [data-testid="stCodeBlock"] > div,
            [data-testid="stChatMessage"] [data-testid="stExpander"] pre {{
                background-color: #f0f0f0 !important;
                color: #333 !important;
            }}
            [data-testid="stChatMessage"] [data-testid="stExpander"] code {{
                background-color: transparent !important;
                color: #333 !important;
            }}
            /* User chat bubbles — white background */
            [data-testid="stChatMessage"]:has(.user-msg-marker) {{
                background-color: rgba(255, 255, 255, 0.92) !important;
                border-radius: 8px !important;
            }}
            </style>
        """, unsafe_allow_html=True)

# Make the main page name stand out in the sidebar navigation
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] li:first-child a span {
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title(CHAT_TITLE)

st.warning(
    "**Prototype Notice:** This is an early-stage prototype application. "
    "Responses may be incomplete or inaccurate. Do not use for operational decisions.",
    icon="⚠️",
)

# Initialize chat history in session state
# If PERSIST_CONVERSATIONS=true, restore the user's last session from disk on first load
PERSIST_CONVERSATIONS = os.getenv("PERSIST_CONVERSATIONS", "false").lower() == "true"
LOGGING_ENABLED = os.getenv("LOGGING_ENABLED", "true").lower() == "true"
CHAT_LOG_DIR = os.getenv("CHAT_LOG_DIR", "chat_logs")

if "messages" not in st.session_state:
    st.session_state.messages = []
    if PERSIST_CONVERSATIONS:
        _log_path = os.path.join(CHAT_LOG_DIR, f"chat_history_{current_user}_latest.json")
        if os.path.exists(_log_path):
            try:
                with open(_log_path) as _f:
                    _saved = json.load(_f)
                st.session_state.messages = _saved.get("messages", [])
            except Exception as _e:
                print(f"Could not restore chat history for {current_user}: {_e}")

# Initialize processing flag to disable input during query execution
if "processing" not in st.session_state:
    st.session_state.processing = False

# Initialize data cache for storing query results across messages
if "query_data_cache" not in st.session_state:
    st.session_state.query_data_cache = {}

# Store last query result for easy plotting
if "last_query_result" not in st.session_state:
    st.session_state.last_query_result = None

# Initialize provider and model selection
# Check for environment variable overrides
env_provider = os.getenv("DEFAULT_PROVIDER", DEFAULT_PROVIDER).lower()
if "selected_provider" not in st.session_state:
    if env_provider == "claude":
        st.session_state.selected_provider = "Claude API"
    elif env_provider == "gemini":
        st.session_state.selected_provider = "Gemini API"
    else:
        st.session_state.selected_provider = "Ollama"

if "selected_model" not in st.session_state:
    env_model = os.getenv("DEFAULT_MODEL", "")
    if env_model:
        st.session_state.selected_model = env_model
    elif st.session_state.selected_provider == "Claude API":
        st.session_state.selected_model = DEFAULT_CLAUDE_MODEL
    elif st.session_state.selected_provider == "Gemini API":
        st.session_state.selected_model = DEFAULT_GEMINI_MODEL
    else:
        st.session_state.selected_model = DEFAULT_OLLAMA_MODEL

# Cache for Ollama models list
if "ollama_models_cache" not in st.session_state:
    st.session_state.ollama_models_cache = None

# Add a clear chat button in the sidebar
with st.sidebar:
    st.header("Chat Controls")

    if _authenticator is not None:
        if user_avatar is not None:
            st.image(user_avatar, width=50)
        st.caption(f"Logged in as: **{current_user}**")
        _authenticator.logout("Logout", "sidebar")

        with st.expander("Edit Profile"):
            new_name = st.text_input(
                "Display name",
                value=st.session_state.get("name", current_user),
                key="edit_profile_name",
            )
            avatar_files = _get_avatar_files()
            if avatar_files:
                st.write("Choose a profile picture:")
                new_avatar = _avatar_selector(
                    key="edit_profile_avatar",
                    current=st.session_state.get("_user_avatar"),
                )
            else:
                new_avatar = st.session_state.get("_user_avatar")
            if st.button("Save Changes", key="save_profile"):
                ok, err = update_user_profile(current_user, new_name.strip(), new_avatar)
                if ok:
                    st.success("Profile updated!")
                    st.rerun()
                else:
                    st.error(f"Failed to save changes: {err}")

        st.divider()

    # Show stop button while processing
    if st.session_state.processing:
        st.warning("⏳ Processing query...")
        if st.button("🛑 Stop Processing", type="primary"):
            st.session_state.processing = False
            st.session_state.messages.append({
                "role": "assistant",
                "content": "⚠️ Processing stopped by user."
            })
            save_chat_history(current_user)
            st.rerun()

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.processing = False
        st.session_state.query_data_cache = {}
        st.session_state.last_query_result = None
        st.rerun()

    # Show current message count
    msg_count = len(st.session_state.messages)
    st.caption(f"Messages in history: {msg_count}")

    # Show data cache status
    cache_size = len(st.session_state.get("query_data_cache", {}))
    if cache_size > 0:
        st.caption(f"Cached queries: {cache_size}")
        if st.button("🧹 Clear Data Cache"):
            st.session_state.query_data_cache = {}
            st.session_state.last_query_result = None
            st.success("Data cache cleared!")
            st.rerun()
    # if msg_count > 20:
    #     st.warning("⚠️ Long conversation history may cause rate limits")

    # =========================================================================
    # AI Model Selector
    # =========================================================================
    st.header("AI Model")

    # Provider selection
    provider_options = ["Ollama", "Claude API", "Gemini API"]
    provider_index = provider_options.index(st.session_state.selected_provider) if st.session_state.selected_provider in provider_options else 0
    selected_provider = st.selectbox(
        "Provider",
        provider_options,
        index=provider_index,
        key="provider_selector",
        help="Select Ollama for local models, Claude API for Anthropic models, or Gemini API for Google models"
    )

    # Update session state if provider changed
    if selected_provider != st.session_state.selected_provider:
        st.session_state.selected_provider = selected_provider
        # Reset model to default for the new provider
        if selected_provider == "Claude API":
            st.session_state.selected_model = DEFAULT_CLAUDE_MODEL
        elif selected_provider == "Gemini API":
            st.session_state.selected_model = DEFAULT_GEMINI_MODEL
        else:
            st.session_state.selected_model = DEFAULT_OLLAMA_MODEL
        st.rerun()

    # Model selection based on provider
    if selected_provider == "Claude API":
        # Claude API selected
        claude_provider = ClaudeProvider()
        if not claude_provider.is_connected():
            st.warning("⚠️ ANTHROPIC_API_KEY not set")
            st.caption("Set the key in .env to use Claude models")
        else:
            st.caption(f"API Key: {claude_provider.get_masked_api_key()}")

        model_options = CLAUDE_MODELS
        default_model = DEFAULT_CLAUDE_MODEL
        model_index = model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else model_options.index(default_model)

        selected_model = st.selectbox(
            "Model",
            model_options,
            index=model_index,
            key="model_selector_claude",
            help="claude-opus-4-5 (most capable), claude-sonnet-4 (balanced), claude-haiku (fast)"
        )
    elif selected_provider == "Gemini API":
        # Gemini API selected
        gemini_provider = GeminiProvider()
        if not gemini_provider.is_connected():
            st.warning("⚠️ GEMINI_API_KEY not set")
            st.caption("Set the key in .env to use Gemini models")
        else:
            st.caption(f"API Key: {gemini_provider.get_masked_api_key()}")

        model_options = GEMINI_MODELS
        default_model = DEFAULT_GEMINI_MODEL
        model_index = model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else model_options.index(default_model)

        selected_model = st.selectbox(
            "Model",
            model_options,
            index=model_index,
            key="model_selector_gemini",
            help="gemini-3-flash-preview (latest), gemini-2.5-flash (stable), gemini-2.5-pro (most capable)"
        )
    else:
        # Ollama selected
        # Fetch models from Ollama (with caching)
        if st.session_state.ollama_models_cache is None:
            try:
                ollama_provider = OllamaProvider()
                st.session_state.ollama_models_cache = ollama_provider.get_available_models()
            except Exception:
                st.session_state.ollama_models_cache = []

        model_options = st.session_state.ollama_models_cache
        if not model_options:
            st.warning("⚠️ No Ollama models found")
            st.caption("Make sure Ollama is running")
            model_options = [DEFAULT_OLLAMA_MODEL]  # Fallback

        # Try to find current model in list, otherwise use default
        if st.session_state.selected_model in model_options:
            model_index = model_options.index(st.session_state.selected_model)
        elif DEFAULT_OLLAMA_MODEL in model_options:
            model_index = model_options.index(DEFAULT_OLLAMA_MODEL)
        else:
            model_index = 0

        selected_model = st.selectbox(
            "Model",
            model_options,
            index=model_index,
            key="model_selector_ollama",
            help="Select from installed Ollama models"
        )

        # Refresh models button
        if st.button("🔄 Refresh Models"):
            st.session_state.ollama_models_cache = None
            st.rerun()

    # Update selected model in session state
    if selected_model != st.session_state.selected_model:
        st.session_state.selected_model = selected_model

    # Show current selection
    st.caption(f"Using: **{st.session_state.selected_model}**")

    st.divider()

    # =========================================================================
    # Connection Status
    # =========================================================================
    st.header("Connection Status")

    # Show connection info based on selected provider
    if selected_provider == "Ollama":
        st.caption(f"Ollama: {OLLAMA_BASE_URL}")
        if OLLAMA_API_MODE == "openai":
            st.caption("API mode: OpenAI-compatible (/v1)")
        else:
            st.caption("API mode: Native Ollama (/api)")

        if st.button("🔍 Check Ollama Connection"):
            with st.spinner("Checking Ollama connection..."):
                try:
                    r = requests.get(OLLAMA_TAGS_URL, timeout=10)
                    r.raise_for_status()
                    st.success("✅ Ollama connection successful!")
                except Exception as e:
                    st.error(f"Error checking Ollama: {str(e)}")
    elif selected_provider == "Claude API":
        # Claude API selected
        if ANTHROPIC_AVAILABLE:
            st.caption("✅ anthropic package installed")
        else:
            st.error("❌ anthropic package not installed")
            st.caption("Run: pip install anthropic")
    else:
        # Gemini API selected
        if GOOGLE_AVAILABLE:
            st.caption("✅ google-generativeai package installed")
        else:
            st.error("❌ google-generativeai package not installed")
            st.caption("Run: pip install google-generativeai")

    # MCP Server connection check
    st.header("SPEAR MCP Server")
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "")
    if MCP_SERVER_URL:
        st.caption(f"Endpoint: {MCP_SERVER_URL}")
        if st.button("🔍 Check MCP Connection"):
            with st.spinner("Checking MCP server connection..."):
                try:
                    # Try the health endpoint first
                    health_url = MCP_SERVER_URL.rstrip('/') + '/health'
                    r = requests.get(health_url, timeout=10)
                    r.raise_for_status()
                    st.success("✅ MCP server connection successful!")
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Cannot connect to MCP server at {MCP_SERVER_URL}")
                    st.caption("Make sure the MCP server is running with: `uv run spear-mcp`")
                except Exception as e:
                    # Health endpoint might not exist, try SSE endpoint
                    try:
                        sse_url = MCP_SERVER_URL.rstrip('/') + '/sse'
                        r = requests.get(sse_url, timeout=5, stream=True)
                        if r.status_code == 200:
                            st.success("✅ MCP server connection successful!")
                        else:
                            st.warning(f"⚠️ MCP server responded with status {r.status_code}")
                    except Exception as e2:
                        st.error(f"❌ MCP connection error: {str(e2)}")
    else:
        st.caption("Using stdio transport (local)")
        st.info("MCP_SERVER_URL not set - using local stdio transport")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_latex_from_text(text: str) -> str:
    """
    Remove LaTeX notation from text and convert to plain text.
    The model sometimes outputs LaTeX despite instructions not to.
    """
    if not text:
        return text

    # Replace \text{...} with just the text (do this first)
    text = re.sub(r'\\text\{([^}]*)\}', r'\1', text)

    # Remove \[ ... \] block equations (keep content) - handle both escaped and raw
    text = re.sub(r'\\\[\s*', '', text)
    text = re.sub(r'\s*\\\]', '', text)
    # Also handle raw [ ] that might remain from LaTeX blocks
    text = re.sub(r'^\[\s*', '', text)
    text = re.sub(r'\s*\]$', '', text)

    # Remove \( ... \) inline math (keep content)
    text = re.sub(r'\\\(', '', text)
    text = re.sub(r'\\\)', '', text)

    # Replace \times with ×
    text = text.replace('\\times', '×')

    # Replace common LaTeX superscripts/subscripts
    text = text.replace('^{-1}', '⁻¹')
    text = text.replace('^{-2}', '⁻²')
    text = text.replace('^{2}', '²')
    text = text.replace('^{3}', '³')
    text = text.replace('_{2}', '₂')
    text = text.replace('^{-5}', '⁻⁵')
    text = text.replace('^{-6}', '⁻⁶')

    # Replace \frac{a}{b} with a/b
    text = re.sub(r'\\frac\{([^}]*)\}\{([^}]*)\}', r'\1/\2', text)

    # Remove remaining LaTeX commands
    text = re.sub(r'\\(cdot|quad|qquad|,|;|!|\s)', ' ', text)

    # Clean up units formatting
    text = text.replace('kg m⁻² s⁻¹', 'kg/m²/s')
    text = text.replace('m⁻²', '/m²')
    text = text.replace('s⁻¹', '/s')

    # Remove standalone [ ] brackets that look like LaTeX remnants
    text = re.sub(r'\[\s*\]', '', text)

    # Clean up multiple spaces
    text = re.sub(r'  +', ' ', text)

    # Clean up spacing around equals signs in formulas
    text = re.sub(r'\s*=\s*', ' = ', text)

    return text.strip()


def save_chat_history(username="default"):
    """
    Save the current chat history to a JSON file for debugging and review.
    When auth is enabled, logs are scoped per user via the username parameter.
    """
    if not LOGGING_ENABLED:
        return

    log_dir = CHAT_LOG_DIR
    os.makedirs(log_dir, exist_ok=True)

    latest_file = os.path.join(log_dir, f"chat_history_{username}_latest.json")

    try:
        with open(latest_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "message_count": len(st.session_state.messages),
                "messages": st.session_state.messages
            }, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving chat history: {e}")


def show_tool_output(result: dict):
    """
    Display structured tool results and optional plots.

    Args:
        result: Dictionary containing tool execution results with 'status', 'tool', and 'data' keys
    """
    if result.get("status") != "ok":
        st.error(result.get("error"))
        return

    # Special handling for NetCDF data queries
    if result["tool"] == "query_netcdf_data" and isinstance(result.get("data"), dict):
        info = result["data"].get("data_info", {})
        st.write(f"**Variable:** {result['data'].get('variable')} — shape {info.get('shape')}")
        plot_data_preview(result["data"])

    # Show full JSON result in an expander
    with st.expander("Show full JSON result"):
        st.json(result)


def plot_data_preview(data_dict: dict):
    """
    Generate a quick matplotlib plot for climate data arrays.

    Args:
        data_dict: Dictionary containing climate data arrays
    """
    try:
        arr = np.array(data_dict.get("data"))
        if arr.ndim == 2:
            st.pyplot(plt.imshow(arr, aspect='auto'))
        elif arr.ndim == 1:
            plt.plot(arr)
            st.pyplot(plt)
    except Exception as e:
        st.info(f"❌ Error plotting data: {e}")


def retrieve_rag_context(query: str, k: int = 5) -> str:
    """
    Retrieve relevant context from the RAG FastAPI service.

    IMPORTANT:
    - Uses POST /query with JSON body: {"query": "...", "k": 5}
    """
    rag_url = os.getenv("RAG_API_URL", "http://localhost:8002").rstrip("/")
    try:
        r = requests.post(
            f"{rag_url}/query",
            json={"query": query, "k": k},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            return ""
        return "\n\n".join([x.get("content", "") for x in results if x.get("content")])
    except Exception as e:
        print(f"RAG retrieval failed: {e}")
        return ""


def is_climate_related_query(text: str) -> bool:
    """
    Check if a query is related to climate/SPEAR data and would benefit from RAG context.
    Returns False for conversational queries, greetings, or follow-up questions.
    """
    text_lower = text.lower().strip()

    # Short queries are usually conversational follow-ups - skip RAG
    if len(text_lower.split()) <= 3:
        # Exception: short but clearly climate-related
        climate_short = ["temperature", "precipitation", "climate", "spear", "weather",
                        "ensemble", "scenario", "historical", "ssp", "netcdf", "variable",
                        "sst", "noaa", "gfdl", "enso", "model", "data"]
        if not any(term in text_lower for term in climate_short):
            return False

    # Skip RAG for greetings and conversational phrases
    # Use word boundary matching for short words to avoid false positives
    # e.g., "no" should not match "noaa", "ok" should not match "token"
    skip_phrases = [
        "hello", "hey", "thanks", "thank you", "okay", "please", "sure",
        "got it", "i see", "continue", "proceed", "go ahead",
        "remember", "recall", "what did", "what was", "you said", "earlier",
        "next", "previous", "last", "again", "repeat", "show me again"
    ]
    # Short words that need word boundary matching
    skip_words = ["hi", "ok", "yes", "no"]

    # Check phrases (substring match is fine for multi-word)
    if any(phrase in text_lower for phrase in skip_phrases):
        return False

    # Check short words with word boundaries
    for word in skip_words:
        if re.search(rf'\b{word}\b', text_lower):
            return False

    # Include RAG for climate-specific queries
    climate_keywords = [
        "climate", "weather", "temperature", "precipitation", "spear", "gfdl",
        "ensemble", "scenario", "ssp5", "historical", "forecast", "model",
        "netcdf", "variable", "data", "analysis", "trend", "projection",
        "atmosphere", "ocean", "sea surface", "enso", "el nino", "la nina",
        "humidity", "pressure", "wind", "radiation", "ice", "snow",
        "sst", "noaa", "ncep", "ecmwf", "reanalysis", "cmip", "ipcc"
    ]
    has_climate_keyword = any(keyword in text_lower for keyword in climate_keywords)

    # Skip for questions about the conversation itself, UNLESS they contain climate keywords
    conversation_refs = ["what are the", "what is the", "what were", "which one",
                        "how many", "tell me", "remind me"]
    if any(ref in text_lower for ref in conversation_refs) and len(text_lower.split()) < 8:
        # But if it has climate keywords, still use RAG
        if not has_climate_keyword:
            return False

    return has_climate_keyword


def is_plot_request(text: str) -> bool:
    """Check if user is asking for a plot/visualization."""
    text_lower = text.lower()
    plot_keywords = ["plot", "chart", "graph", "visualize", "visualization", "show me a", "draw", "display"]
    return any(kw in text_lower for kw in plot_keywords)


def extract_plot_data_from_cache() -> str:
    """Extract data from the last query result for plotting."""
    if not st.session_state.get("last_query_result"):
        return ""

    result = st.session_state.last_query_result
    if result.get("status") != "ok":
        return ""

    data = result.get("data", {})
    if not isinstance(data, dict):
        return ""

    # Extract the raw data values
    raw_values = data.get("data", [])
    variable = data.get("variable", "unknown")
    coords = data.get("coordinates", {})
    time_values = coords.get("time", {}).get("values", [])

    # Flatten the data if it's nested (handles multi-dimensional arrays)
    flat_values = []
    def flatten(arr):
        for item in arr:
            if isinstance(item, list):
                flatten(item)
            else:
                flat_values.append(item)
    if raw_values:
        flatten(raw_values)

    if not flat_values:
        return ""

    # For large datasets (like daily data over a region), compute spatial average per time step
    data_info = data.get("data_info", {})
    shape = data_info.get("shape", [])

    # Handle different data shapes
    if len(shape) == 3:  # [time, lat, lon]
        n_time, n_lat, n_lon = shape
        # Compute spatial average for each time step
        spatial_size = n_lat * n_lon
        if len(flat_values) == n_time * spatial_size:
            averaged_values = []
            for t in range(n_time):
                start_idx = t * spatial_size
                end_idx = start_idx + spatial_size
                time_slice = flat_values[start_idx:end_idx]
                avg = sum(time_slice) / len(time_slice)
                averaged_values.append(avg)
            flat_values = averaged_values

    # Extract time labels
    time_labels = []
    if time_values:
        for t in time_values[:len(flat_values)]:
            # Extract just the date part
            if isinstance(t, str):
                time_labels.append(t[:10])  # "2020-06-01T12:00:00" -> "2020-06-01"
            else:
                time_labels.append(str(t))

    # Convert based on variable type
    if variable == "pr":
        # Precipitation: convert kg/m²/s to mm/day
        converted = [round(v * 86400, 2) for v in flat_values]
        units = "mm/day"
        ylabel = "Precipitation (mm/day)"
        title = "Precipitation"
        plot_type = "bar" if len(converted) <= 12 else "line"
        color = "steelblue"
    elif variable in ["tas", "tasmax", "tasmin"]:
        # Temperature: convert K to °C
        converted = [round(v - 273.15, 1) for v in flat_values]
        units = "°C"
        ylabel = "Temperature (°C)"
        var_names = {"tas": "Temperature", "tasmax": "Max Temperature", "tasmin": "Min Temperature"}
        title = var_names.get(variable, "Temperature")
        plot_type = "line"
        color = "red" if variable == "tasmax" else "blue" if variable == "tasmin" else "orange"
    else:
        # Generic handling - no conversion
        converted = [round(v, 4) if isinstance(v, float) else v for v in flat_values]
        units = data.get("attributes", {}).get("units", "")
        ylabel = f"{variable} ({units})" if units else variable
        title = variable
        plot_type = "line"
        color = "steelblue"

    # Use month names for 12-value monthly data
    if len(converted) == 12 and not time_labels:
        time_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Limit to reasonable size for the prompt (max 100 points)
    if len(converted) > 100:
        # Sample every Nth point
        step = len(converted) // 100
        converted = converted[::step]
        time_labels = time_labels[::step] if time_labels else []

    x_data = time_labels if time_labels else list(range(len(converted)))

    return f"""
CACHED DATA FOR PLOTTING ({variable}, converted to {units}):
x = {x_data[:20]}{'...' if len(x_data) > 20 else ''}
y = {converted[:20]}{'...' if len(converted) > 20 else ''}
Total points: {len(converted)}
variable = "{variable}"
units = "{units}"

Call create_plot with this data. Use plot_type="{plot_type}", color="{color}".
"""


def build_augmented_user_prompt(user_text: str) -> str:
    """
    Pull RAG context and return a user prompt augmented with it.
    RAG context is always fetched (when enabled) and the model decides whether to use it.
    Can be disabled by setting RAG_ENABLED=false in .env
    """
    augmented = user_text

    # Add plot reminder if user is asking for a plot
    if is_plot_request(user_text):
        cached_data = extract_plot_data_from_cache()
        if cached_data:
            # We have cached data - tell the model to use it
            augmented = (
                f"{user_text}\n\n"
                "---\n"
                "[SYSTEM REMINDER: User is asking for a PLOT. You have cached data available.\n"
                "1. Call the create_plot tool with the data below\n"
                "2. Do NOT query data again - use the cached values\n"
                "3. Pass plot_config as a dict (not a string)]\n"
                f"{cached_data}"
            )
        else:
            # No cached data - model needs to query first
            augmented = (
                f"{user_text}\n\n"
                "---\n"
                "[SYSTEM REMINDER: User is asking for a PLOT but no data is cached.\n"
                "You must first query the data using query_netcdf_data, then create the plot.]\n"
            )
        return augmented

    # Check if RAG is enabled (default: true)
    rag_enabled = os.getenv("RAG_ENABLED", "true").lower() == "true"
    if not rag_enabled:
        return user_text

    # COMMENTED OUT: Previously only fetched RAG for climate-related queries.
    # Now we always fetch RAG and let the model decide whether to use the context.
    # Uncomment to re-enable keyword filtering:
    # if not is_climate_related_query(user_text):
    #     return user_text

    # Reduced from 5 to 2 to avoid overwhelming the context
    rag_k = int(os.getenv("RAG_TOP_K", "2"))
    rag_context = retrieve_rag_context(user_text, k=rag_k)
    if not rag_context.strip():
        return user_text

    # Put the user's question FIRST, then context as supplementary
    return (
        f"{user_text}\n\n"
        "---\n"
        "[Supplementary SPEAR background info - use only if relevant to the question above]:\n"
        f"{rag_context}"
    )


def build_conversation_context(messages: list[dict]) -> str:
    """
    Build a brief summary of the conversation context to help the model
    maintain continuity across turns.

    Extracts key parameters and goals mentioned by the user.
    """
    context_parts = []

    # Track mentioned parameters
    scenario = None
    ensemble = None
    frequency = None
    variable = None
    region = None
    year = None
    user_goal = None

    # Scan through user messages to extract context
    for msg in messages:
        if msg.get("role") != "user":
            continue

        content = msg.get("content", "").lower()

        # Detect scenario
        if "historical" in content:
            scenario = "historical"
        elif "ssp5" in content or "ssp5-85" in content or "future" in content:
            scenario = "scenarioSSP5-85"

        # Detect ensemble member
        if "ensemble member 1" in content or "member 1" in content or "r1i1p1f1" in content:
            ensemble = "r1i1p1f1"
        elif "ensemble" in content:
            # Try to extract ensemble number
            match = re.search(r'ensemble\s*(?:member)?\s*(\d+)', content)
            if match:
                ensemble = f"r{match.group(1)}i1p1f1"

        # Detect frequency
        if "6hr" in content or "6-hour" in content or "6 hour" in content:
            frequency = "6hr"
        elif "daily" in content or "day" in content:
            frequency = "day"
        elif "monthly" in content or "amon" in content:
            frequency = "Amon"

        # Detect variable
        if "precip" in content or " pr " in content or content.startswith("pr "):
            variable = "pr (precipitation)"
        elif "temp" in content or " tas " in content or " ta " in content:
            variable = "tas (temperature)"

        # Detect region
        if "mexico" in content:
            region = "Mexico (14°N-33°N, 86°W-118°W)"
        elif "us" in content or "united states" in content:
            region = "United States"

        # Detect year
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', content)
        if year_match:
            year = year_match.group(1)

        # Detect goals/actions
        if "metadata" in content or "meta data" in content:
            user_goal = "get metadata"
        elif "plot" in content or "visualiz" in content:
            user_goal = "create plot/visualization"
        elif "data" in content and ("get" in content or "fetch" in content or "retrieve" in content):
            user_goal = "retrieve data"

    # Build context summary
    if scenario:
        context_parts.append(f"Scenario: {scenario}")
    if ensemble:
        context_parts.append(f"Ensemble: {ensemble}")
    if frequency:
        context_parts.append(f"Frequency: {frequency}")
    if variable:
        context_parts.append(f"Variable: {variable}")
    if region:
        context_parts.append(f"Region: {region}")
    if year:
        context_parts.append(f"Year: {year}")
    if user_goal:
        context_parts.append(f"Goal: {user_goal}")

    if not context_parts:
        return ""

    return "\n\n[CONVERSATION CONTEXT - Parameters mentioned so far: " + ", ".join(context_parts) + "]"


def build_recent_conversation_summary(messages: list[dict], max_turns: int = 4) -> str:
    """
    Build a brief summary of the most recent conversation turns.
    This helps the model remember what was just discussed.
    """
    if len(messages) < 2:
        return ""

    # Get recent user-assistant exchanges (excluding tool messages)
    recent = []
    for msg in messages[-(max_turns * 2):]:
        role = msg.get("role")
        if role == "user":
            content = msg.get("content", "")[:100]  # Truncate long messages
            recent.append(f"User: {content}")
        elif role == "assistant":
            content = msg.get("content", "")[:150]
            # Skip tool execution markers
            if not content.startswith("_Accessing") and not content.startswith("🔧"):
                recent.append(f"You said: {content}")

    if not recent:
        return ""

    return "\n\n[RECENT CONVERSATION REMINDER:\n" + "\n".join(recent[-4:]) + "\n]"


def build_ollama_messages(messages: list[dict]) -> list[dict]:
    """
    Build Ollama-compatible messages, ensuring the system prompt is included first.
    Uses content_for_model when available (for RAG-augmented prompts).
    Includes conversation context summary to help maintain continuity.
    """
    # Build conversation context (climate parameters)
    context_summary = build_conversation_context(messages)

    # Build recent conversation summary (general memory aid)
    recent_summary = build_recent_conversation_summary(messages)

    # Combine system prompt with context
    enhanced_system = SYSTEM_PROMPT
    if context_summary:
        enhanced_system = SYSTEM_PROMPT + context_summary
    if recent_summary:
        enhanced_system = enhanced_system + recent_summary

    # Add confidence assessment reminder at the END (most prominent position)
    confidence_reminder = """

[MANDATORY OUTPUT FORMAT]
Your response MUST end with this exact format:
---
**Confidence Assessment:**
📊 **Overall Confidence: [X]%** [emoji based on score]
- 🔍 **Data Accuracy:** [X]%
- 🧪 **Scientific Explanation:** [X]%
- 🖥️ **Model Information:** [X]%
✅/⚠️ Key factors affecting confidence
---
DO NOT skip this section."""
    enhanced_system = enhanced_system + confidence_reminder

    cleaned = []
    for m in messages:
        if m.get("role") == "system":
            continue
        # Use content_for_model if available (RAG-augmented), otherwise use content
        msg_copy = m.copy()
        if "content_for_model" in msg_copy:
            msg_copy["content"] = msg_copy.pop("content_for_model")
        cleaned.append(msg_copy)
    return [{"role": "system", "content": enhanced_system}, *cleaned]


def _ollama_native_stream(payload: dict):
    final_message = {}
    yielded = False
    with requests.post(OLLAMA_CHAT_URL, json=payload, stream=True, timeout=120) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            data = json.loads(line)
            if data.get("error"):
                raise RuntimeError(data["error"])
            message = data.get("message", {})
            if message:
                # Preserve tool_calls across chunks (important for qwen2.5:7b)
                if message.get("tool_calls"):
                    final_message["tool_calls"] = message["tool_calls"]
                if message.get("content") is not None:
                    final_message["content"] = message["content"]
                if message.get("role"):
                    final_message["role"] = message["role"]
            content = message.get("content")
            if content:
                yielded = True
                yield content, final_message
            if data.get("done"):
                break
    if not yielded:
        yield "", final_message


def _ollama_openai_stream(payload: dict):
    final_message = {"role": "assistant"}
    yielded = False
    content_buffer = ""
    tool_calls_buffer = {}
    with requests.post(OLLAMA_CHAT_URL, json=payload, stream=True, timeout=120) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            if not line.startswith("data:"):
                continue
            data_str = line.split("data:", 1)[1].strip()
            if data_str == "[DONE]":
                break
            data = json.loads(data_str)
            if data.get("error"):
                raise RuntimeError(data["error"])
            choice = data.get("choices", [{}])[0]
            delta = choice.get("delta", {})
            if delta.get("content"):
                content_buffer += delta["content"]
                final_message["content"] = content_buffer
                yielded = True
                yield delta["content"], final_message
            for tool_call in delta.get("tool_calls", []) or []:
                index = tool_call.get("index", 0)
                entry = tool_calls_buffer.setdefault(
                    index,
                    {"id": None, "type": tool_call.get("type", "function"), "function": {"name": "", "arguments": ""}},
                )
                if tool_call.get("id"):
                    entry["id"] = tool_call["id"]
                func_delta = tool_call.get("function", {})
                if func_delta.get("name"):
                    entry["function"]["name"] += func_delta["name"]
                if func_delta.get("arguments"):
                    entry["function"]["arguments"] += func_delta["arguments"]
                final_message["tool_calls"] = list(tool_calls_buffer.values())
        if "tool_calls" in final_message and not yielded:
            yield "", final_message


def ollama_chat_stream(payload: dict):
    """
    Stream a chat response from Ollama, yielding (chunk, final_message).
    Ensures at least one yield even if the model returns tool calls without text.
    """
    if OLLAMA_API_MODE == "openai":
        yield from _ollama_openai_stream(payload)
    else:
        yield from _ollama_native_stream(payload)


# ============================================================================
# CHAT INTERFACE
# ============================================================================

# Always display welcome message at the top (even with chat history)
with st.chat_message("assistant", avatar=bot_avatar):
    st.markdown(WELCOME_MESSAGE)

# Add separator if there's chat history
if len(st.session_state.messages) > 0:
    st.markdown("---")

# Display chat history
# Intermediate assistant messages (with tool_calls) and tool result messages
# are folded into the final assistant bubble so no extra chat bubbles appear.
_pending_tool_results = []

for message in st.session_state.messages:
    if message.get("role") == "system":
        continue

    # Collect tool result data — rendered inside the final assistant bubble
    if message.get("role") == "tool":
        # Use full _display_data if available, else fall back to (possibly truncated) content
        _pending_tool_results.append(message.get("_display_data") or message.get("content", ""))
        continue

    # Intermediate assistant message — no separate bubble needed
    if message.get("role") == "assistant" and message.get("tool_calls"):
        continue

    # User message — reset accumulators
    if message.get("role") == "user":
        _pending_tool_results = []

    with st.chat_message(message["role"], avatar=user_avatar if message["role"] == "user" else bot_avatar):
        if message["role"] == "user":
            st.markdown('<div class="user-msg-marker" style="display:none;"></div>', unsafe_allow_html=True)
        content = message["content"]

        if message.get("role") == "assistant":
            # Tool results expander (raw data returned by each tool)
            if _pending_tool_results:
                with st.expander("🔧 Tool Results", expanded=False):
                    for raw in _pending_tool_results:
                        if isinstance(raw, dict):
                            st.json(raw)
                        else:
                            try:
                                st.json(json.loads(raw))
                            except Exception:
                                st.code(raw, language="json")
                _pending_tool_results = []

        if isinstance(content, str):
            st.markdown(clean_latex_from_text(content))
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    continue
                if hasattr(item, "text"):
                    st.markdown(clean_latex_from_text(item.text))

        # Re-render saved plot image (after text so it stays at the bottom)
        if message.get("role") == "assistant" and message.get("_plot_png"):
            st.image(message["_plot_png"], use_container_width=True)

            @st.fragment
            def _plot_download(png_data, btn_key):
                st.download_button(
                    label="📥 Download Plot (PNG)",
                    data=png_data,
                    file_name="climate_plot.png",
                    mime="image/png",
                    key=btn_key,
                )
            _plot_download(message["_plot_png"], f"dl_plot_{id(message)}")

# Handle user input - disabled while processing
if prompt := st.chat_input(
    CHAT_INPUT_PLACEHOLDER,
    disabled=st.session_state.processing
):
    # Set processing flag to disable input
    st.session_state.processing = True

    # Show the user's *clean* message in UI
    with st.chat_message("user", avatar=user_avatar):
        st.markdown('<div class="user-msg-marker" style="display:none;"></div>', unsafe_allow_html=True)
        st.markdown(prompt)

    # Build the augmented prompt (RAG is injected here, NOT as role=system)
    augmented_prompt = build_augmented_user_prompt(prompt)

    # Store BOTH clean and augmented - display clean, send augmented to model
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,  # Store clean prompt for display
        "content_for_model": augmented_prompt  # Store augmented for model
    })

    # Generate assistant response
    with st.chat_message("assistant", avatar=bot_avatar):
        msg_placeholder = st.empty()
        msg_placeholder.markdown("_Thinking..._")
        full_resp = ""

        try:
            # ====================================================================
            # Initialize the LLM provider based on session state selection
            # ====================================================================
            if st.session_state.selected_provider == "Claude API":
                provider_type = "claude"
            elif st.session_state.selected_provider == "Gemini API":
                provider_type = "gemini"
            else:
                provider_type = "ollama"
            current_model = st.session_state.selected_model
            provider = get_provider(provider_type)

            # Build the enhanced system prompt (with context)
            context_summary = build_conversation_context(st.session_state.messages)
            recent_summary = build_recent_conversation_summary(st.session_state.messages)
            enhanced_system = SYSTEM_PROMPT
            if context_summary:
                enhanced_system = SYSTEM_PROMPT + context_summary
            if recent_summary:
                enhanced_system = enhanced_system + recent_summary

            # Confidence assessment reminder (disabled — interferes with tool calling)
            # confidence_reminder = """
            # [OPTIONAL] If providing a final answer (not calling tools), please include a confidence assessment."""
            # enhanced_system = enhanced_system + confidence_reminder

            # ====================================================================
            # PHASE 1: Initial LLM Response (may include tool calls)
            # ====================================================================
            final_msg = {}
            for chunk, msg in provider.chat_stream(
                messages=st.session_state.messages,
                tools=OLLAMA_TOOLS,
                model=current_model,
                system_prompt=enhanced_system,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            ):
                if chunk:
                    full_resp += chunk
                    # Clean LaTeX from display
                    clean_resp = clean_latex_from_text(full_resp)
                    msg_placeholder.markdown(clean_resp + "▌")
                if msg is not None:
                    final_msg = msg

            # Extract tool calls (unified format from provider)
            tool_calls = provider.extract_tool_calls(final_msg)

            # Debug: Log what we got from the model
            print(f"DEBUG: Provider={provider_type}, Model={current_model}")
            print(f"DEBUG: full_resp length: {len(full_resp)}, tool_calls count: {len(tool_calls)}")
            if tool_calls:
                print(f"DEBUG: Tool calls: {[tc.get('name') for tc in tool_calls]}")
            else:
                print("DEBUG: No tool calls received from model")

            # Retry logic for empty responses (Gemini sometimes returns nothing)
            max_retries = 3
            retry_count = 0
            while not full_resp.strip() and not tool_calls and retry_count < max_retries:
                retry_count += 1
                print(f"WARNING: Empty response from {provider_type}, retrying ({retry_count}/{max_retries})...")
                msg_placeholder.markdown(f"_Retrying (attempt {retry_count + 1})..._")

                # Retry the LLM call
                full_resp = ""
                final_msg = {}
                for chunk, msg in provider.chat_stream(
                    messages=st.session_state.messages,
                    tools=OLLAMA_TOOLS,
                    model=current_model,
                    system_prompt=enhanced_system,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                ):
                    if chunk:
                        full_resp += chunk
                    if msg is not None:
                        final_msg = msg

                tool_calls = provider.extract_tool_calls(final_msg)
                print(f"DEBUG: Retry {retry_count} - full_resp length: {len(full_resp)}, tool_calls count: {len(tool_calls)}")

            # If still empty after retries, remove user message and show error without saving
            if not full_resp.strip() and not tool_calls:
                print(f"ERROR: Model returned empty after {max_retries + 1} attempts")
                # Remove the user message we just added - don't pollute history with failed attempts
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()
                # Show error but DON'T save it to history
                error_message = f"⚠️ The model failed to respond after {max_retries + 1} attempts. Please try your query again."
                msg_placeholder.markdown(error_message)
                st.session_state.processing = False
                st.stop()  # Stop execution here - don't save anything

            # Handle case where model returns empty content with tool calls (e.g., qwen2.5:7b)
            if tool_calls and not full_resp.strip():
                full_resp = "_Accessing SPEAR climate data..._\n\n"
                msg_placeholder.markdown(full_resp)

            # Clean LaTeX from the response before further processing
            full_resp = clean_latex_from_text(full_resp)

            # ====================================================================
            # PHASE 2: Tool Execution Loop (continues until model is done)
            # ====================================================================
            if tool_calls:
                current_msg = final_msg
                max_tool_iterations = 10  # Safety limit to prevent infinite loops
                iteration = 0
                tool_execution_log = []  # Track tool executions separately
                size_warning_encountered = False  # Flag to stop loop if query too large
                _pending_plot_png = None  # PNG bytes from create_plot, saved on final message
                # Track the current response content for this iteration
                current_response_content = full_resp

                while tool_calls and iteration < max_tool_iterations and not size_warning_encountered:
                    iteration += 1

                    # IMPORTANT: Append assistant message WITH tool_calls metadata
                    # This is required for Claude API to properly match tool_result with tool_use
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": current_response_content,
                        "tool_calls": tool_calls,  # Store tool calls for Claude API
                    })

                    # Execute each tool requested (unified format from provider)
                    for tool_call in tool_calls:
                        # Unified format: {"id": "...", "name": "tool_name", "arguments": {...}}
                        tool_name = tool_call.get("name")
                        tool_args = tool_call.get("arguments", {}) or {}
                        tool_call_id = tool_call.get("id") or f"tool_call_{iteration}_{tool_name}"

                        # Arguments should already be a dict, but handle string case for safety
                        if isinstance(tool_args, str):
                            try:
                                tool_args = json.loads(tool_args)
                            except json.JSONDecodeError:
                                tool_args = {}

                        # Log tool execution
                        tool_log_entry = f"🔧 **Using tool:** `{tool_name}`"
                        tool_execution_log.append(tool_log_entry)

                        current_display = full_resp + "\n\n" + "\n".join(tool_execution_log)
                        msg_placeholder.markdown(current_display)

                        with st.spinner(f"Executing {tool_name}..."):
                            result = query_mcp_tool(tool_name, tool_args)

                        if result.get("status") == "ok":
                            tool_execution_log[-1] += " ✅"

                            # Add transfer stats to the log if available
                            transfer_stats = result.get("transfer_stats")
                            if transfer_stats:
                                stats_str = f" _(⏱️ {transfer_stats.get('elapsed_time_seconds', 0)}s"
                                if transfer_stats.get('response_kb', 0) > 0:
                                    stats_str += f" | 📦 {transfer_stats.get('response_kb', 0):.1f} KB"
                                if transfer_stats.get('data_points', 0) > 0:
                                    stats_str += f" | 📊 {transfer_stats.get('data_points', 0):,} points"
                                stats_str += ")_"
                                tool_execution_log[-1] += stats_str

                            # Save query results to session state for later use
                            if tool_name == "query_netcdf_data":
                                st.session_state.last_query_result = result
                                st.session_state.query_data_cache[json.dumps(tool_args, sort_keys=True)] = result
                                print(f"[SESSION] Saved query result to session state")

                            if tool_name == "create_plot":
                                fig = result.get("data", {}).get("figure")
                                if fig is not None:
                                    buf = BytesIO()
                                    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
                                    buf.seek(0)
                                    plot_png = buf.getvalue()

                                    st.image(plot_png, use_container_width=True)

                                    @st.fragment
                                    def _live_plot_download(png_data):
                                        st.download_button(
                                            label="📥 Download Plot (PNG)",
                                            data=png_data,
                                            file_name=f"climate_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                            mime="image/png",
                                        )
                                    _live_plot_download(plot_png)

                                    _pending_plot_png = plot_png

                                    import matplotlib.pyplot as _plt
                                    _plt.close(fig)
                                else:
                                    with st.expander("🔧 Tool Results", expanded=False):
                                        st.json(result.get("data"))
                            else:
                                with st.expander("🔧 Tool Results", expanded=False):
                                    st.json(result.get("data"))
                        else:
                            error_type = result.get("error", "")
                            if (
                                "Query too large" in error_type
                                or "Invalid latitude range" in error_type
                                or "Invalid longitude range" in error_type
                            ):
                                if "Query too large" in error_type:
                                    tool_execution_log[-1] += " ⚠️ Query too large - prevented execution"
                                else:
                                    tool_execution_log[-1] += " ⚠️ Invalid coordinates - prevented execution"

                                size_warning_encountered = True

                                warning_msg = result.get("warning_message", "")
                                if warning_msg:
                                    st.warning("Query Issue")
                                    st.markdown(warning_msg)

                                    data_shape = result.get("data_shape", {})
                                    if data_shape:
                                        def _fmt(v):
                                            return f"{v:,}" if isinstance(v, int) else str(v)
                                        with st.expander("📊 Query Details", expanded=True):
                                            st.warning("Query size information:", icon="📊")
                                            st.write(f"**Time points:** {_fmt(data_shape.get('time_points','N/A'))}")
                                            st.write(f"**Latitude points:** {_fmt(data_shape.get('lat_points','N/A'))}")
                                            st.write(f"**Longitude points:** {_fmt(data_shape.get('lon_points','N/A'))}")
                                            st.write(f"**Total data points:** {_fmt(data_shape.get('total_data_points','N/A'))}")
                                            st.write(f"**Estimated tokens:** {_fmt(result.get('estimated_tokens','N/A'))}")
                            else:
                                tool_execution_log[-1] += f" ❌ Error: {result.get('error')}"

                        current_display = full_resp + "\n\n" + "\n".join(tool_execution_log)
                        msg_placeholder.markdown(current_display)

                        try:
                            content_str = json.dumps(result, default=str)
                        except (TypeError, ValueError, json.JSONDecodeError) as e:
                            content_str = f"Tool result serialization error: {str(e)}\nRaw result: {str(result)}"

                        # Truncate large tool results to prevent context overflow
                        MAX_TOOL_RESULT_LENGTH = 5000  # ~1250 tokens
                        if len(content_str) > MAX_TOOL_RESULT_LENGTH:
                            original_length = len(content_str)
                            print(f"DEBUG: Truncating {tool_name} result: {original_length} chars -> {MAX_TOOL_RESULT_LENGTH} chars")

                            # For search results, provide a summary
                            if tool_name == "search_spear_variables" and result.get("status") == "ok":
                                data = result.get("data", [])
                                total_results = len(data) if isinstance(data, list) else 0
                                truncated_data = data[:10] if isinstance(data, list) else data

                                truncated_result = {
                                    "status": "ok",
                                    "tool": tool_name,
                                    "data": truncated_data,
                                    "summary": f"Found {total_results} total results. Showing first {len(truncated_data)}. Full results available in UI.",
                                    "truncated": True
                                }
                                content_str = json.dumps(truncated_result, default=str)
                                print(f"DEBUG: Truncated to {total_results} results -> showing first {len(truncated_data)}")
                            else:
                                # For other large results, truncate with a note
                                truncated = content_str[:MAX_TOOL_RESULT_LENGTH]
                                content_str = truncated + f"\n\n[... truncated {original_length - MAX_TOOL_RESULT_LENGTH} chars to save context. Full results visible in UI.]"

                        st.session_state.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": content_str,        # truncated — for LLM context only
                            "_display_data": result,       # full result — for UI display only
                        })

                    if size_warning_encountered:
                        final_msg_text = "\n\n**⚠️ Query size exceeds limits. Please provide a smaller query or choose one of the alternatives above.**"
                        current_display = full_resp + "\n\n" + "\n".join(tool_execution_log) + final_msg_text
                        msg_placeholder.markdown(current_display)

                        st.session_state.messages.append({"role": "assistant", "content": current_display})
                        save_chat_history(current_user)
                        break

                    current_display = full_resp + "\n\n" + "\n".join(tool_execution_log)
                    msg_placeholder.markdown(current_display + "\n\n_Processing..._")

                    # Follow-up call to the provider with tool results
                    text_response = ""
                    current_msg = {}
                    for chunk, msg in provider.chat_stream(
                        messages=st.session_state.messages,
                        tools=OLLAMA_TOOLS,
                        model=current_model,
                        system_prompt=enhanced_system,
                        temperature=TEMPERATURE,
                        max_tokens=MAX_TOKENS,
                    ):
                        if chunk:
                            text_response += chunk
                            # Clean LaTeX from display
                            clean_text = clean_latex_from_text(text_response)
                            msg_placeholder.markdown(current_display + "\n\n" + clean_text + "▌")
                        if msg is not None:
                            current_msg = msg

                    # Extract tool calls from follow-up response
                    tool_calls = provider.extract_tool_calls(current_msg)

                    # Clean LaTeX before storing
                    if text_response:
                        text_response = clean_latex_from_text(text_response)

                    # Update tracking: current_response_content is what THIS iteration produced
                    current_response_content = text_response
                    # Accumulate for display
                    if text_response:
                        full_resp += "\n\n" + text_response

                # After the loop, add tool execution log and final message
                if tool_execution_log:
                    full_resp += "\n\n" + "\n".join(tool_execution_log)

                msg_placeholder.markdown(full_resp)

                # Only append final assistant message if the last response had no tool calls
                # (meaning the loop exited because tool_calls was empty, not due to iteration limit)
                # Save full_resp (includes tool execution log) not current_response_content
                if not tool_calls and full_resp.strip():
                    msg_data = {"role": "assistant", "content": full_resp}
                    if _pending_plot_png is not None:
                        msg_data["_plot_png"] = _pending_plot_png
                    st.session_state.messages.append(msg_data)
                save_chat_history(current_user)

            else:
                # No tool use, just display the response
                msg_placeholder.markdown(full_resp)
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
                save_chat_history(current_user)

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            msg_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            save_chat_history(current_user)

    # Reset processing flag after response is complete
    # This runs outside the try/except to ensure the input is re-enabled
    st.session_state.processing = False


