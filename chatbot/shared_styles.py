"""
shared_styles.py — Shared background and theme CSS for all Streamlit pages.

Call apply_sidebar_background() on sub-pages to style only the sidebar.
Call apply_background() for the full-page treatment (main page).
"""

import os
import base64
import streamlit as st


def _get_bg_data():
    """Load the background image and return (b64_data, mime_type) or (None, None)."""
    bg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "background")
    bg_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

    if not os.path.isdir(bg_dir):
        return None, None

    bg_candidates = sorted(
        f for f in os.listdir(bg_dir)
        if os.path.splitext(f)[1].lower() in bg_exts
    )
    if not bg_candidates:
        return None, None

    bg_path = os.path.join(bg_dir, bg_candidates[0])
    with open(bg_path, "rb") as f:
        bg_b64 = base64.b64encode(f.read()).decode()

    bg_ext = os.path.splitext(bg_candidates[0])[1].lower().lstrip(".")
    bg_mime = "jpeg" if bg_ext in ("jpg", "jpeg") else bg_ext
    return bg_b64, bg_mime


def apply_sidebar_background():
    """Inject background image CSS for the sidebar only (sub-pages)."""
    bg_b64, bg_mime = _get_bg_data()
    if bg_b64 is None:
        return

    st.markdown(f"""
        <style>
        [data-testid="stSidebar"] {{
            background-image:
                linear-gradient(rgba(0, 0, 0, 0.60), rgba(0, 0, 0, 0.60)),
                url("data:image/{bg_mime};base64,{bg_b64}") !important;
            background-size: cover !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
        }}
        [data-testid="stSidebar"] * {{
            color: white !important;
        }}
        [data-testid="stSidebar"] details,
        [data-testid="stSidebar"] [data-testid="stExpander"] {{
            background-color: transparent !important;
            border-left: none !important;
        }}
        [data-testid="stSidebarNav"] li:first-child a span {{
            font-weight: 700 !important;
            font-size: 1.1rem !important;
        }}
        </style>
    """, unsafe_allow_html=True)


def apply_background():
    """Inject full background image and overlay CSS (main page)."""
    bg_b64, bg_mime = _get_bg_data()
    if bg_b64 is None:
        return

    st.markdown(f"""
        <style>
        .stApp {{
            background-image:
                linear-gradient(rgba(255, 255, 255, 0.80), rgba(255, 255, 255, 0.80)),
                url("data:image/{bg_mime};base64,{bg_b64}") !important;
            background-size: cover !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
        }}
        [data-testid="stSidebar"] {{
            background-image:
                linear-gradient(rgba(0, 0, 0, 0.60), rgba(0, 0, 0, 0.60)),
                url("data:image/{bg_mime};base64,{bg_b64}") !important;
            background-size: cover !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
        }}
        .stApp * {{
            color: black !important;
        }}
        [data-testid="stAlert"] {{
            background-color: rgba(255, 220, 0, 0.35) !important;
            border-color: rgba(200, 160, 0, 0.9) !important;
        }}
        .stApp code {{
            background-color: rgba(255, 220, 0, 0.45) !important;
            color: black !important;
            border-radius: 3px !important;
            padding: 1px 4px !important;
        }}
        [data-testid="stSidebar"] * {{
            color: white !important;
        }}
        [data-testid="stSidebar"] details,
        [data-testid="stSidebar"] [data-testid="stExpander"] {{
            background-color: transparent !important;
            border-left: none !important;
        }}
        [data-testid="stHeader"] {{
            background: transparent !important;
        }}
        [data-testid="stMain"] [data-testid="stExpander"] details {{
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
        [data-testid="stSidebarNav"] li:first-child a span {{
            font-weight: 700 !important;
            font-size: 1.1rem !important;
        }}
        </style>
    """, unsafe_allow_html=True)
