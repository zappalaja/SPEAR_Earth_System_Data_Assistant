"""
auth_setup.py — Authentication gate for the SPEAR Climate Chatbot.

Controlled by AUTH_ENABLED in chatbot/.env:
  AUTH_ENABLED=false  → no login screen, app runs as normal (default)
  AUTH_ENABLED=true   → login required; credentials stored in users.yaml

Returns (authenticator, username) to the caller.
When auth is disabled, returns (None, "default").
"""

import os
import streamlit as st

AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"

USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.yaml")
AVATARS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatars")
BOT_AVATAR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_avatar")

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_config(yaml, SafeLoader):
    with open(USERS_FILE) as f:
        return yaml.load(f, Loader=SafeLoader)


def _save_config(yaml, config):
    with open(USERS_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def _get_avatar_files():
    """Return sorted list of image filenames found in the avatars directory."""
    if not os.path.isdir(AVATARS_DIR):
        return []
    return sorted(
        f for f in os.listdir(AVATARS_DIR)
        if os.path.splitext(f)[1].lower() in _IMAGE_EXTS
    )


def _avatar_selector(key="avatar_select", current=None):
    """
    Render a row of image thumbnails with a radio picker below.
    Works inside and outside st.form contexts.
    Returns the selected filename, or current if no images are available.
    """
    files = _get_avatar_files()
    if not files:
        st.caption("No avatar images found in `chatbot/avatars/`. Drop images there and restart.")
        return current

    from PIL import Image as PILImage

    cols = st.columns(len(files))
    for col, fname in zip(cols, files):
        with col:
            try:
                st.image(PILImage.open(os.path.join(AVATARS_DIR, fname)), width=60)
            except Exception:
                st.caption(fname)

    default_idx = files.index(current) if current in files else 0
    return st.radio(
        "Avatar",
        options=files,
        index=default_idx,
        horizontal=True,
        format_func=lambda x: os.path.splitext(x)[0],
        label_visibility="collapsed",
        key=key,
    )


def get_user_avatar(username):
    """
    Return the user's avatar as a PIL Image, or None for the Streamlit default icon.
    Filename is read from session state (cached at login); PIL Image is also cached.
    Safe to call when auth is disabled.
    """
    if not AUTH_ENABLED or username == "default":
        return None

    avatar_filename = st.session_state.get("_user_avatar")
    if not avatar_filename:
        return None

    # Return cached PIL image if already loaded this session
    if "_user_avatar_img" in st.session_state:
        return st.session_state._user_avatar_img

    img_path = os.path.join(AVATARS_DIR, avatar_filename)
    if os.path.exists(img_path):
        try:
            from PIL import Image as PILImage
            img = PILImage.open(img_path).copy()  # copy closes the file handle
            st.session_state._user_avatar_img = img
            return img
        except Exception:
            return None
    return None


def get_bot_avatar():
    """
    Return the chatbot's avatar as a PIL Image, or None to use the Streamlit default.
    Loads the first image file found in bot_avatar/ and caches it in session state.
    """
    if "_bot_avatar_img" in st.session_state:
        return st.session_state._bot_avatar_img

    if not os.path.isdir(BOT_AVATAR_DIR):
        return None

    candidates = sorted(
        f for f in os.listdir(BOT_AVATAR_DIR)
        if os.path.splitext(f)[1].lower() in _IMAGE_EXTS
    )
    if not candidates:
        return None

    img_path = os.path.join(BOT_AVATAR_DIR, candidates[0])
    try:
        from PIL import Image as PILImage
        img = PILImage.open(img_path).copy()
        st.session_state._bot_avatar_img = img
        return img
    except Exception:
        return None


def render_sidebar_profile(page_key: str = ""):
    """Render the user profile section in the sidebar. Safe to call on any page.

    Args:
        page_key: unique prefix to avoid widget key collisions across pages.
    """
    if not AUTH_ENABLED:
        return
    if not st.session_state.get("authentication_status"):
        return

    username = st.session_state.get("username", "unknown")
    user_avatar = get_user_avatar(username)
    pk = f"{page_key}_" if page_key else ""

    with st.sidebar:
        if user_avatar is not None:
            st.image(user_avatar, width=50)
        st.caption(f"Logged in as: **{st.session_state.get('name', username)}**")

        try:
            import streamlit_authenticator as stauth
            import yaml
            from yaml.loader import SafeLoader
            config = _load_config(yaml, SafeLoader)
            authenticator = stauth.Authenticate(
                config["credentials"],
                config["cookie"]["name"],
                config["cookie"]["key"],
                config["cookie"]["expiry_days"],
            )
            authenticator.logout("Logout", "sidebar", key=f"{pk}logout")
        except Exception:
            pass

        with st.expander("Edit Profile"):
            new_name = st.text_input(
                "Display name",
                value=st.session_state.get("name", username),
                key=f"{pk}edit_profile_name",
            )
            avatar_files = _get_avatar_files()
            if avatar_files:
                st.write("Choose a profile picture:")
                new_avatar = _avatar_selector(
                    key=f"{pk}edit_profile_avatar",
                    current=st.session_state.get("_user_avatar"),
                )
            else:
                new_avatar = st.session_state.get("_user_avatar")
            if st.button("Save Changes", key=f"{pk}save_profile"):
                ok, err = update_user_profile(username, new_name.strip(), new_avatar)
                if ok:
                    st.success("Profile updated!")
                    st.rerun()
                else:
                    st.error(f"Failed to save changes: {err}")

        st.divider()


def update_user_profile(username, new_name, new_avatar_file):
    """
    Save display name and/or avatar changes for a user to users.yaml.
    Also updates the relevant session state keys so changes are immediate.
    Returns (True, None) on success, (False, error_message) on failure.
    """
    try:
        import yaml
        from yaml.loader import SafeLoader
        if not os.path.exists(USERS_FILE):
            return False, f"users.yaml not found at {USERS_FILE}"
        config = _load_config(yaml, SafeLoader)
        users = (config.get("credentials") or {}).get("usernames") or {}
        # Case-insensitive match — streamlit-authenticator lowercases session username
        yaml_key = next((k for k in users if k.lower() == username.lower()), None)
        if yaml_key is None:
            return False, f"Username '{username}' not found in users.yaml (found: {list(users.keys())})"
        username = yaml_key  # use the correctly-cased key for all subsequent writes

        if new_name:
            users[username]["name"] = new_name
            st.session_state["name"] = new_name

        if new_avatar_file and new_avatar_file != st.session_state.get("_user_avatar"):
            users[username]["avatar"] = new_avatar_file
            st.session_state._user_avatar = new_avatar_file
            # Clear cached PIL image so it reloads from the new file
            st.session_state.pop("_user_avatar_img", None)

        _save_config(yaml, config)
        return True, None
    except Exception as e:
        return False, str(e)


# ── Registration form ────────────────────────────────────────────────────────

def _register_form(yaml, bcrypt, SafeLoader):
    """Render the registration form and write to users.yaml on success."""
    with st.form("register_form"):
        st.subheader("Create Account")
        new_username = st.text_input("Username", placeholder="no spaces")
        new_name = st.text_input("Display name", placeholder="how you appear in the sidebar")
        new_password = st.text_input("Password", type="password")
        new_confirm = st.text_input("Confirm password", type="password")

        st.write("Choose a profile picture:")
        selected_avatar = _avatar_selector(key="register_avatar")

        submitted = st.form_submit_button("Register", use_container_width=True)

    if not submitted:
        return

    if not new_username or " " in new_username:
        st.error("Username cannot be empty or contain spaces.")
        return
    if not new_name.strip():
        st.error("Display name is required.")
        return
    if len(new_password) < 8:
        st.error("Password must be at least 8 characters.")
        return
    if new_password != new_confirm:
        st.error("Passwords do not match.")
        return

    config = _load_config(yaml, SafeLoader)
    creds = config.setdefault("credentials", {})
    if not creds.get("usernames"):
        creds["usernames"] = {}
    users = creds["usernames"]

    if new_username in users:
        st.error(f"Username '{new_username}' is already taken.")
        return

    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    users[new_username] = {
        "name": new_name.strip(),
        "password": hashed,
        "avatar": selected_avatar,
    }
    _save_config(yaml, config)

    st.session_state._auth_view = "login"
    st.session_state._register_success = new_name.strip()
    st.rerun()


# ── Auth gate ────────────────────────────────────────────────────────────────

def _cache_avatar(config, username):
    """Load avatar filename from config into session state (once per session)."""
    if "_user_avatar" not in st.session_state:
        users = (config.get("credentials") or {}).get("usernames") or {}
        # Case-insensitive match for the same reason as update_user_profile
        yaml_key = next((k for k in users if k.lower() == username.lower()), username)
        st.session_state._user_avatar = (users.get(yaml_key) or {}).get("avatar") or None


def setup_auth():
    """
    Initialize authentication if AUTH_ENABLED=true.

    Returns:
        (authenticator, username) — authenticator is None when auth is disabled.

    Calls st.stop() if auth is enabled but the user is not authenticated,
    which halts Streamlit execution before any app content is rendered.
    """
    if not AUTH_ENABLED:
        return None, "default"

    try:
        import yaml
        import bcrypt
        import streamlit_authenticator as stauth
        from yaml.loader import SafeLoader
    except ImportError as e:
        st.error(
            f"Auth dependencies missing: {e}\n\n"
            "Run: `pip install streamlit-authenticator PyYAML bcrypt`"
        )
        st.stop()

    if not os.path.exists(USERS_FILE):
        st.error(
            "AUTH_ENABLED=true but `users.yaml` was not found.\n\n"
            "Add users with: `python manage_users.py add`"
        )
        st.stop()

    config = _load_config(yaml, SafeLoader)

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )

    # Already authenticated — skip login UI entirely
    if st.session_state.get("authentication_status") is True:
        username = st.session_state.get("username", "unknown")
        _cache_avatar(config, username)
        return authenticator, username

    # Not yet authenticated — show Login / Register views
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True):
            st.session_state._auth_view = "login"
            st.rerun()
    with col2:
        if st.button("Register", use_container_width=True):
            st.session_state._auth_view = "register"
            st.rerun()

    if st.session_state.get("_register_success"):
        name = st.session_state.pop("_register_success")
        st.success(f"Account created for **{name}**. You can now log in.")

    if st.session_state.get("_auth_view", "login") == "login":
        try:
            authenticator.login()
        except Exception as e:
            st.error(f"Login error: {e}")
            st.stop()
    else:
        _register_form(yaml, bcrypt, SafeLoader)

    status = st.session_state.get("authentication_status")

    if status is False:
        st.error("Incorrect username or password.")
        st.stop()
    elif status is None:
        st.stop()

    # Successful fresh login — cache avatar before rerun
    username = st.session_state.get("username", "unknown")
    _cache_avatar(config, username)
    st.rerun()
