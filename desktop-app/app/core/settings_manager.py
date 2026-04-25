"""
Settings Manager — centralized read/write for API keys and model preferences.

Reads from and writes to the .env file at the repository root.
API keys are stored as environment variables (GROQ_API_KEY, etc.).
Model preferences are stored as MODEL_GROQ, MODEL_ANTHROPIC, MODEL_GEMINI.

Other modules should use get_setting() to read values, so changes
made in the Settings page are immediately available everywhere.
"""

import os
from pathlib import Path

# ── .env file location ──────────────────────────────────────────

_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"

# ── AI Service Definitions ──────────────────────────────────────

AI_SERVICES = {
    "groq": {
        "label": "Groq (Transcription)",
        "key_env": "GROQ_API_KEY",
        "model_env": "MODEL_GROQ",
        "description": (
            "Groq provides ultra-fast inference for Whisper speech-to-text. "
            "Used to transcribe session recordings into text. "
            "Get a free key at https://console.groq.com"
        ),
        "models": [
            ("whisper-large-v3", "Whisper Large V3 — best accuracy"),
            ("whisper-large-v3-turbo", "Whisper Large V3 Turbo — faster"),
            ("distil-whisper-large-v3-en", "Distil Whisper — fastest, English only"),
        ],
        "default_model": "whisper-large-v3",
    },
    "anthropic": {
        "label": "Anthropic (Summarization)",
        "key_env": "ANTHROPIC_API_KEY",
        "model_env": "MODEL_ANTHROPIC",
        "description": (
            "Anthropic's Claude generates structured session summaries — "
            "narrative recap, key events, lore notes, and cliffhangers. "
            "Get a key at https://console.anthropic.com"
        ),
        "models": [
            ("claude-sonnet-4-20250514", "Claude Sonnet 4 — balanced quality/speed"),
            ("claude-3-5-haiku-20241022", "Claude 3.5 Haiku — fastest, cheapest"),
            ("claude-3-7-sonnet-20250219", "Claude 3.7 Sonnet — high quality"),
        ],
        "default_model": "claude-sonnet-4-20250514",
    },
    "gemini": {
        "label": "Gemini (Narration & TTS)",
        "key_env": "GEMINI_API_KEY",
        "model_env": "MODEL_GEMINI",
        "description": (
            "Google Gemini transforms summaries into dramatic narration scripts, "
            "then converts them to cinematic audio via TTS. "
            "Get a free key at https://aistudio.google.com/apikey"
        ),
        "models": [
            ("gemini-2.5-flash", "Gemini 2.5 Flash — fast, great quality"),
            ("gemini-2.0-flash", "Gemini 2.0 Flash — stable, reliable"),
            ("gemini-2.5-pro", "Gemini 2.5 Pro — highest quality, slower"),
        ],
        "default_model": "gemini-2.5-flash",
    },
}


# ── Read / Write helpers ────────────────────────────────────────

def _load_env_dict() -> dict[str, str]:
    """Parse .env file into a dict. Preserves order."""
    env = {}
    if _ENV_PATH.exists():
        for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def _save_env_dict(env: dict[str, str]):
    """Write dict back to .env file."""
    lines = [f"{k}={v}" for k, v in env.items()]
    _ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_setting(key: str, default: str = "") -> str:
    """Get a setting — checks os.environ first, then .env file."""
    val = os.environ.get(key, "")
    if val:
        return val
    env = _load_env_dict()
    return env.get(key, default)


def get_api_key(service_id: str) -> str:
    """Get the API key for a service (e.g. 'groq')."""
    info = AI_SERVICES.get(service_id, {})
    key_env = info.get("key_env", "")
    return get_setting(key_env) if key_env else ""


def get_model(service_id: str) -> str:
    """Get the selected model for a service, falling back to default."""
    info = AI_SERVICES.get(service_id, {})
    model_env = info.get("model_env", "")
    default = info.get("default_model", "")
    return get_setting(model_env, default) if model_env else default


def save_all(settings: dict[str, str]):
    """
    Save a dict of key=value pairs to .env and update os.environ.

    Args:
        settings: e.g. {"GROQ_API_KEY": "gsk_...", "MODEL_GROQ": "whisper-large-v3"}
    """
    env = _load_env_dict()
    for k, v in settings.items():
        env[k] = v
        os.environ[k] = v
    _save_env_dict(env)
