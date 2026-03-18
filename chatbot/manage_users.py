#!/usr/bin/env python3
"""
manage_users.py — Add, remove, and list SPEAR Chatbot users.

Usage:
  python manage_users.py add               # interactive prompt
  python manage_users.py remove <username>
  python manage_users.py list
"""

import sys
import os
import getpass

AVATARS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatars")
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _get_avatar_files():
    if not os.path.isdir(AVATARS_DIR):
        return []
    return sorted(
        f for f in os.listdir(AVATARS_DIR)
        if os.path.splitext(f)[1].lower() in _IMAGE_EXTS
    )

try:
    import yaml
    import bcrypt
except ImportError:
    print("Missing dependencies. Run: pip install PyYAML bcrypt")
    sys.exit(1)

USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.yaml")


def load_config():
    if not os.path.exists(USERS_FILE):
        print(f"users.yaml not found at {USERS_FILE}")
        sys.exit(1)
    with open(USERS_FILE) as f:
        return yaml.safe_load(f)


def save_config(config):
    with open(USERS_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def cmd_add():
    config = load_config()
    creds = config.setdefault("credentials", {})
    if not creds.get("usernames"):
        creds["usernames"] = {}
    users = creds["usernames"]

    print("--- Add User ---")
    username = input("Username (no spaces): ").strip()
    if not username or " " in username:
        print("Invalid username.")
        sys.exit(1)
    if username in users:
        print(f"User '{username}' already exists. Remove first to re-add.")
        sys.exit(1)

    name = input("Display name: ").strip()
    # email = input("Email: ").strip()  # not collected for now

    avatar_files = _get_avatar_files()
    selected_avatar = None
    if avatar_files:
        print("Available avatars:")
        for i, f in enumerate(avatar_files):
            print(f"  {i + 1}. {f}")
        av_input = input(f"Avatar number [1-{len(avatar_files)}, skip]: ").strip()
        try:
            av_index = int(av_input) - 1
            selected_avatar = avatar_files[av_index] if 0 <= av_index < len(avatar_files) else None
        except (ValueError, IndexError):
            selected_avatar = None
    else:
        print("(No avatar images found in chatbot/avatars/ — skipping)")

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    entry = {
        # "email": email,  # not collected for now
        "name": name,
        "password": hashed,
    }
    if selected_avatar:
        entry["avatar"] = selected_avatar
    users[username] = entry

    save_config(config)
    print(f"User '{username}' added.")


def cmd_remove(username):
    config = load_config()
    users = config.get("credentials", {}).get("usernames", {})

    if username not in users:
        print(f"User '{username}' not found.")
        sys.exit(1)

    confirm = input(f"Remove user '{username}'? [y/N] ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        sys.exit(0)

    del users[username]
    save_config(config)
    print(f"User '{username}' removed.")


def cmd_list():
    config = load_config()
    users = config.get("credentials", {}).get("usernames", {})

    if not users:
        print("No users configured.")
        return

    print(f"{'Username':<20} {'Display Name':<25} {'Avatar'}")
    print("-" * 60)
    for uname, info in sorted(users.items()):
        print(f"{uname:<20} {info.get('name', ''):<25} {info.get('avatar', '—')}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "add":
        cmd_add()
    elif command == "remove":
        if len(sys.argv) < 3:
            print("Usage: python manage_users.py remove <username>")
            sys.exit(1)
        cmd_remove(sys.argv[2])
    elif command == "list":
        cmd_list()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
