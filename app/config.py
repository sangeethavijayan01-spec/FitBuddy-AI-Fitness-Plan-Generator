"""Central configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def get_database_url() -> str:
    return env("DATABASE_URL") or f"sqlite:///{(BASE_DIR / 'fitbuddy.db').as_posix()}"


def get_gemini_api_key() -> str:
    return env("GEMINI_API_KEY")


def api_key_is_configured() -> bool:
    key = get_gemini_api_key()
    return bool(key) and not key.lower().startswith("your_")


def get_gemini_model() -> str:
    return env("GEMINI_MODEL", "gemini-3.8-flash")


def get_gemini_timeout_seconds() -> float:
    try:
        value = float(env("GEMINI_TIMEOUT_SECONDS", "90"))
        return value if value > 0 else 90.0
    except ValueError:
        return 90.0


def get_secret_key() -> str:
    return env("SECRET_KEY", "dev-only-change-this-secret")


def get_admin_username() -> str:
    return env("ADMIN_USERNAME", "admin")


def get_admin_password() -> str:
    return env("ADMIN_PASSWORD")
