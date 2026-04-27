"""
config.py — Central configuration for RPG Session Recorder.

Loads API keys from .env file, defines player mapping,
audio settings, and session directory helpers.
"""

import os
import sys
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# When frozen, look for .env next to the .exe
if getattr(sys, "frozen", False):
    load_dotenv(Path(sys.executable).resolve().parent / ".env")
else:
    load_dotenv()

# --- API Keys (loaded from .env) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# --- Audio Settings ---
SAMPLE_RATE = 44100
AUDIO_DEVICE = None   # None = auto-detect default device
NUM_CHANNELS = 1      # 1 for laptop mic, 5 for Focusrite Scarlett 6i6

# --- Player Mapping ---
# Maps channel index to player name.
# When using 1 channel (laptop), only channel_0 is used.
# When using 5 channels (Focusrite), all 5 are active.
PLAYERS = {
    "channel_0": "Dungeon Master",
    "channel_1": "Player 1",
    "channel_2": "Player 2",
    "channel_3": "Player 3",
    "channel_4": "Player 4",
}

# --- Silence Stripping Settings ---
MIN_SILENCE_LEN = 700    # milliseconds of silence to trigger a split
SILENCE_THRESH = -40      # dBFS threshold for silence detection
SILENCE_PADDING = 300     # milliseconds of padding to keep around speech

# --- Session Directory ---
# When frozen (.exe), store sessions next to the executable.
if getattr(sys, "frozen", False):
    SESSIONS_DIR = Path(sys.executable).resolve().parent / "sessions"
else:
    SESSIONS_DIR = Path(__file__).parent / "sessions"


def get_session_dir() -> Path:
    """
    Create and return a session directory for today.

    Format: sessions/YYYY-MM-DD/
    If a folder for today already exists, appends _2, _3, etc.
    Creates the full subdirectory structure (raw/, processed/, transcripts/).

    Returns:
        Path to the session directory.
    """
    today = date.today().isoformat()  # e.g. "2026-04-25"
    session_path = SESSIONS_DIR / today

    # Handle same-day sessions by appending a counter
    if session_path.exists():
        counter = 2
        while (SESSIONS_DIR / f"{today}_{counter}").exists():
            counter += 1
        session_path = SESSIONS_DIR / f"{today}_{counter}"

    # Create subdirectories
    (session_path / "raw").mkdir(parents=True, exist_ok=True)
    (session_path / "processed").mkdir(parents=True, exist_ok=True)
    (session_path / "transcripts").mkdir(parents=True, exist_ok=True)

    return session_path


def get_active_players(num_channels: int) -> dict:
    """
    Return a filtered PLAYERS dict based on how many channels are in use.

    Args:
        num_channels: Number of active audio channels (1 for laptop, 5 for Focusrite).

    Returns:
        Dict mapping channel keys to player names for active channels only.
    """
    return {
        f"channel_{i}": PLAYERS.get(f"channel_{i}", f"Channel {i}")
        for i in range(num_channels)
    }
