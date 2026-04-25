"""
processor.py — Silence stripping module.

Uses pydub to detect and remove silent sections from recorded audio.
Each channel is processed independently, keeping only speech segments
with small padding around them.

Requires ffmpeg installed on the system.
"""

import shutil
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import split_on_silence

from config import MIN_SILENCE_LEN, SILENCE_THRESH, SILENCE_PADDING


def _check_ffmpeg():
    """
    Verify ffmpeg is available on the system.

    Raises:
        RuntimeError: If ffmpeg is not found in PATH.
    """
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg not found! pydub requires ffmpeg for audio processing.\n"
            "Install it:\n"
            "  Windows: choco install ffmpeg  (or download from https://ffmpeg.org/download.html)\n"
            "  macOS:   brew install ffmpeg\n"
            "  Linux:   sudo apt install ffmpeg"
        )


def process_channel(
    input_path: Path,
    output_path: Path,
    min_silence_len: int = MIN_SILENCE_LEN,
    silence_thresh: int = SILENCE_THRESH,
    padding: int = SILENCE_PADDING,
) -> dict:
    """
    Strip silence from a single audio channel.

    How it works:
    1. Loads the .wav file
    2. Splits audio on silent sections (configurable threshold + duration)
    3. Concatenates the non-silent chunks with small padding between them
    4. Saves the result

    Args:
        input_path: Path to the raw .wav file.
        output_path: Path where the processed .wav will be saved.
        min_silence_len: Minimum length of silence (ms) to trigger a split.
        silence_thresh: Silence threshold in dBFS (e.g., -40 means anything
                        quieter than -40 dBFS is considered silence).
        padding: Milliseconds of silence to keep around each speech chunk.

    Returns:
        Dict with processing stats: original_duration, processed_duration, reduction_pct.
    """
    _check_ffmpeg()

    # Load the audio file
    audio = AudioSegment.from_wav(str(input_path))
    original_duration = len(audio)  # in milliseconds

    # Split on silence — returns list of non-silent AudioSegment chunks
    chunks = split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=padding,  # keep this much silence on each side of a chunk
    )

    if not chunks:
        # If the entire file is silence, save an empty-ish file
        print(f"  Warning: {input_path.name} is entirely silent.")
        # Save a very short silent segment so downstream code has a file to work with
        silent = AudioSegment.silent(duration=100)
        silent.export(str(output_path), format="wav")
        return {
            "original_duration_ms": original_duration,
            "processed_duration_ms": 100,
            "reduction_pct": 99.9,
        }

    # Concatenate all non-silent chunks
    processed = chunks[0]
    for chunk in chunks[1:]:
        processed += chunk

    processed_duration = len(processed)

    # Save processed audio
    output_path.parent.mkdir(parents=True, exist_ok=True)
    processed.export(str(output_path), format="wav")

    reduction = (1 - processed_duration / original_duration) * 100 if original_duration > 0 else 0

    return {
        "original_duration_ms": original_duration,
        "processed_duration_ms": processed_duration,
        "reduction_pct": round(reduction, 1),
    }


def process_session(session_dir: Path) -> list[dict]:
    """
    Process all raw channel files in a session directory.

    Reads from session_dir/raw/channel_*.wav
    Writes to session_dir/processed/channel_*.wav

    Args:
        session_dir: Path to the session directory.

    Returns:
        List of processing stats dicts (one per channel).
    """
    session_dir = Path(session_dir)
    raw_dir = session_dir / "raw"
    processed_dir = session_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Find all channel files, sorted by channel number
    raw_files = sorted(raw_dir.glob("channel_*.wav"))

    if not raw_files:
        print(f"No raw channel files found in {raw_dir}")
        return []

    results = []
    for raw_file in raw_files:
        output_file = processed_dir / raw_file.name
        print(f"Processing {raw_file.name}...")
        stats = process_channel(raw_file, output_file)
        stats["channel"] = raw_file.stem  # e.g. "channel_0"
        results.append(stats)
        print(f"  {stats['original_duration_ms']/1000:.1f}s → "
              f"{stats['processed_duration_ms']/1000:.1f}s "
              f"({stats['reduction_pct']}% reduction)")

    return results


# --- Standalone test ---
if __name__ == "__main__":
    import sys

    print("=== Processor Module Test ===\n")

    # Check ffmpeg first
    try:
        _check_ffmpeg()
        print("ffmpeg: OK\n")
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    # Look for the most recent session directory
    from config import SESSIONS_DIR
    if not SESSIONS_DIR.exists():
        print(f"No sessions directory found at {SESSIONS_DIR}")
        print("Run recorder.py first to create a recording.")
        sys.exit(1)

    sessions = sorted(SESSIONS_DIR.iterdir())
    if not sessions:
        print("No session folders found. Run recorder.py first.")
        sys.exit(1)

    latest = sessions[-1]
    print(f"Processing latest session: {latest.name}\n")

    results = process_session(latest)

    print(f"\nProcessed {len(results)} channel(s).")
    for r in results:
        print(f"  {r['channel']}: {r['reduction_pct']}% silence removed")
