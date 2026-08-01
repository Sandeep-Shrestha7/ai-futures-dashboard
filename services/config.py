from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables reliably regardless of the directory used to
# launch Streamlit. Search the project folder first, then its parent folder.
SERVICE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SERVICE_DIR.parent
ENV_CANDIDATES = (
    PROJECT_DIR / ".env",
    PROJECT_DIR.parent / ".env",
    Path.cwd() / ".env",
)

_loaded_env_path = ""
for env_path in ENV_CANDIDATES:
    if env_path.is_file():
        load_dotenv(dotenv_path=env_path, override=True)
        _loaded_env_path = str(env_path)
        break
else:
    # Preserve normal python-dotenv discovery as a final fallback.
    load_dotenv(override=True)


def _get_secret(name: str, default: str = "") -> str:
    """Read from environment, with optional Streamlit secrets fallback."""
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st
        secret = st.secrets.get(name, default)
        return str(secret).strip() if secret is not None else default
    except Exception:
        return default


@dataclass(frozen=True)
class Settings:
    tradovate_username: str = _get_secret("TRADOVATE_USERNAME")
    tradovate_password: str = _get_secret("TRADOVATE_PASSWORD")
    tradovate_app_id: str = _get_secret("TRADOVATE_APP_ID", "AI Futures Dashboard")
    tradovate_app_version: str = _get_secret("TRADOVATE_APP_VERSION", "1.0")
    tradovate_cid: str = _get_secret("TRADOVATE_CID")
    tradovate_sec: str = _get_secret("TRADOVATE_SEC")
    tradovate_device_id: str = _get_secret("TRADOVATE_DEVICE_ID")
    tradovate_demo: bool = _get_secret("TRADOVATE_DEMO", "true").lower() == "true"
    finnhub_key: str = _get_secret("FINNHUB_API_KEY")
    alphavantage_key: str = _get_secret("ALPHAVANTAGE_API_KEY")
    enable_order_execution: bool = _get_secret("ENABLE_ORDER_EXECUTION", "false").lower() == "true"
    loaded_env_path: str = _loaded_env_path


settings = Settings()
