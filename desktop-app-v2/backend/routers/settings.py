"""Settings API — manage .env API keys."""

import os
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import dotenv_values, set_key

router = APIRouter()

_ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class SettingsUpdate(BaseModel):
    groq_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None


def _mask(key: str | None) -> str:
    """Mask an API key for display."""
    if not key:
        return ""
    if len(key) <= 8:
        return "***"
    return key[:4] + "***" + key[-4:]


@router.get("/")
async def get_settings():
    """Get current settings with masked API keys."""
    env = dotenv_values(str(_ENV_PATH)) if _ENV_PATH.exists() else {}
    return {
        "groq_api_key": _mask(env.get("GROQ_API_KEY")),
        "anthropic_api_key": _mask(env.get("ANTHROPIC_API_KEY")),
        "gemini_api_key": _mask(env.get("GEMINI_API_KEY")),
    }


@router.put("/")
async def update_settings(data: SettingsUpdate):
    """Save API keys to .env file."""
    # Create .env if it doesn't exist
    if not _ENV_PATH.exists():
        _ENV_PATH.touch()

    if data.groq_api_key is not None:
        set_key(str(_ENV_PATH), "GROQ_API_KEY", data.groq_api_key)
    if data.anthropic_api_key is not None:
        set_key(str(_ENV_PATH), "ANTHROPIC_API_KEY", data.anthropic_api_key)
    if data.gemini_api_key is not None:
        set_key(str(_ENV_PATH), "GEMINI_API_KEY", data.gemini_api_key)

    return {"status": "saved"}
