"""
merger.py — Transcript merging module.

Loads per-channel transcripts, sorts all segments chronologically
by timestamp, and outputs a single merged transcript with player labels.
"""

import json
from pathlib import Path


def merge_transcripts(session_dir: Path, players_map: dict) -> Path:
    """
    Merge all per-channel transcripts into one chronologically sorted file.

    How it works:
    1. Loads all channel_*.json files from transcripts/
    2. Flattens all segments into a single list
    3. Sorts by start timestamp
    4. Formats each line as: [MM:SS] Player Name: text
    5. Saves to transcripts/merged.txt

    Args:
        session_dir: Path to the session directory.
        players_map: Dict mapping channel keys to player names.

    Returns:
        Path to the merged transcript file.
    """
    session_dir = Path(session_dir)
    transcripts_dir = session_dir / "transcripts"
    transcript_files = sorted(transcripts_dir.glob("channel_*.json"))

    if not transcript_files:
        print(f"No transcript files found in {transcripts_dir}")
        return transcripts_dir / "merged.txt"

    # Collect all segments with player info
    all_segments = []
    for tf in transcript_files:
        with open(tf, "r", encoding="utf-8") as f:
            data = json.load(f)

        player = data.get("player", tf.stem)
        for seg in data.get("segments", []):
            all_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "player": player,
            })

    # Sort by start timestamp
    all_segments.sort(key=lambda s: s["start"])

    # Format as readable transcript
    lines = []
    for seg in all_segments:
        # Convert seconds to MM:SS
        minutes = int(seg["start"] // 60)
        seconds = int(seg["start"] % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"

        lines.append(f"[{timestamp}] {seg['player']}: {seg['text']}")

    # Save merged transcript
    merged_path = transcripts_dir / "merged.txt"
    with open(merged_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Merged {len(all_segments)} segments from {len(transcript_files)} channel(s)")
    print(f"Saved to: {merged_path}")

    return merged_path


# --- Standalone test ---
if __name__ == "__main__":
    import sys
    from config import SESSIONS_DIR, get_active_players, NUM_CHANNELS

    print("=== Merger Module Test ===\n")

    if not SESSIONS_DIR.exists():
        print(f"No sessions directory found at {SESSIONS_DIR}")
        print("Run recorder.py, processor.py, and transcriber.py first.")
        sys.exit(1)

    sessions = sorted(SESSIONS_DIR.iterdir())
    if not sessions:
        print("No session folders found.")
        sys.exit(1)

    latest = sessions[-1]
    print(f"Merging transcripts for session: {latest.name}\n")

    players = get_active_players(NUM_CHANNELS)
    merged_path = merge_transcripts(latest, players)

    # Show preview
    if merged_path.exists():
        content = merged_path.read_text(encoding="utf-8")
        line_count = len(content.splitlines())
        print(f"\n--- Merged Transcript Preview ({line_count} lines) ---")
        for line in content.splitlines()[:20]:
            print(f"  {line}")
        if line_count > 20:
            print(f"  ... ({line_count - 20} more lines)")
