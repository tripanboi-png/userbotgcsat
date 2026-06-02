"""
Configuration module for Telegram Userbot.
Loads all environment variables and validates them.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_env(key: str, required: bool = True, default=None):
    value = os.environ.get(key, default)
    if required and not value:
        raise ValueError(f"[CONFIG] Missing required environment variable: {key}")
    return value


# ─── Telegram ───────────────────────────────────────────────────────────────
API_ID: int = int(get_env("API_ID"))
API_HASH: str = get_env("API_HASH")
OWNER_ID: int = int(get_env("OWNER_ID"))

# ─── MongoDB ────────────────────────────────────────────────────────────────
MONGO_URI: str = get_env("MONGO_URI")
DB_NAME: str = get_env("DB_NAME", required=False, default="userbot_db")

# ─── Session ────────────────────────────────────────────────────────────────
OWNER_SESSION: str = get_env("OWNER_SESSION", required=False, default="")

# ─── General ────────────────────────────────────────────────────────────────
LOG_LEVEL: str = get_env("LOG_LEVEL", required=False, default="INFO")
FLOOD_SLEEP_THRESHOLD: int = int(get_env("FLOOD_SLEEP_THRESHOLD", required=False, default="60"))
BROADCAST_DELAY: float = float(get_env("BROADCAST_DELAY", required=False, default="1.5"))
