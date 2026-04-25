"""
transcriber.py — Audio transcription module using Groq Whisper API.

Sends processed audio files to Groq's Whisper Large V3 model
and returns timestamped transcription segments per channel.
"""

import json
from pathlib import Path
from groq import Groq

from config import GROQ_API_KEY

# Model can be overridden via Settings page (stored in .env as MODEL_GROQ)
def _get_groq_model() -> str:
    import os
    return os.environ.get("MODEL_GROQ", "whisper-large-v3")


def transcribe_channel(audio_path: Path, player_name: str) -> dict:
    """
    Transcribe a single audio channel using Groq Whisper API.

    How it works:
    1. Opens the processed .wav file
    2. Sends it to Groq's Whisper Large V3 model
    3. Parses the verbose JSON response to extract timestamped segments
    4. Returns structured data with player name and segments

    Args:
        audio_path: Path to the processed .wav file.
        player_name: Name of the player for this channel (e.g., "Dungeon Master").

    Returns:
        Dict with structure:
        {
            "player": "Dungeon Master",
            "segments": [
                {"start": 0.0, "end": 2.5, "text": "You enter the dungeon..."},
                ...
            ]
        }
    """
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to your .env file.\n"
            "Get a key at: https://console.groq.com/keys"
        )

    client = Groq(api_key=GROQ_API_KEY)

    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=(audio_path.name, audio_file),
            model=_get_groq_model(),
            response_format="verbose_json",
            language="en",
        )

    # Parse segments from the response
    segments = []
    if hasattr(transcription, "segments") and transcription.segments:
        for seg in transcription.segments:
            segments.append({
                "start": seg.get("start", seg.start) if hasattr(seg, "start") else seg.get("start", 0),
                "end": seg.get("end", seg.end) if hasattr(seg, "end") else seg.get("end", 0),
                "text": (seg.get("text", seg.text) if hasattr(seg, "text") else seg.get("text", "")).strip(),
            })

    return {
        "player": player_name,
        "segments": segments,
    }


def transcribe_session(session_dir: Path, players_map: dict) -> list[dict]:
    """
    Transcribe all processed channel files in a session.

    Reads from session_dir/processed/channel_*.wav
    Saves per-channel transcripts to session_dir/transcripts/channel_*.json

    Args:
        session_dir: Path to the session directory.
        players_map: Dict mapping channel keys to player names,
                     e.g. {"channel_0": "Dungeon Master", ...}

    Returns:
        List of transcript dicts (one per channel).
    """
    session_dir = Path(session_dir)
    processed_dir = session_dir / "processed"
    transcripts_dir = session_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    processed_files = sorted(processed_dir.glob("channel_*.wav"))

    if not processed_files:
        print(f"No processed channel files found in {processed_dir}")
        return []

    results = []
    for audio_file in processed_files:
        channel_key = audio_file.stem  # e.g. "channel_0"
        player_name = players_map.get(channel_key, channel_key)

        print(f"Transcribing {audio_file.name} ({player_name})...")
        transcript = transcribe_channel(audio_file, player_name)

        # Save to JSON
        json_path = transcripts_dir / f"{channel_key}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, indent=2, ensure_ascii=False)

        segment_count = len(transcript["segments"])
        print(f"  → {segment_count} segment(s) saved to {json_path.name}")

        results.append(transcript)

    return results


# --- Standalone test ---
if __name__ == "__main__":
    import sys
    from config import SESSIONS_DIR, get_active_players, NUM_CHANNELS

    print("=== Transcriber Module Test ===\n")

    if not GROQ_API_KEY:
        print("GROQ_API_KEY not set in .env file.")
        print("Add your key to .env and try again.")
        print("Get a key at: https://console.groq.com/keys")
        sys.exit(1)

    if not SESSIONS_DIR.exists():
        print(f"No sessions directory found at {SESSIONS_DIR}")
        print("Run recorder.py and processor.py first.")
        sys.exit(1)

    sessions = sorted(SESSIONS_DIR.iterdir())
    if not sessions:
        print("No session folders found. Run recorder.py and processor.py first.")
        sys.exit(1)

    latest = sessions[-1]
    print(f"Transcribing latest session: {latest.name}\n")

    players = get_active_players(NUM_CHANNELS)
    results = transcribe_session(latest, players)

    print(f"\nTranscribed {len(results)} channel(s).")
    for r in results:
        total_text = " ".join(s["text"] for s in r["segments"])
        preview = total_text[:100] + "..." if len(total_text) > 100 else total_text
        print(f"  {r['player']}: {preview}")
