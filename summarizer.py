"""
summarizer.py — Session summarization module using Claude API.

Sends the merged transcript to Anthropic's Claude model
with an RPG scribe system prompt to generate a structured summary.
"""

from pathlib import Path
from anthropic import Anthropic

from config import ANTHROPIC_API_KEY

# Model can be overridden via Settings page (stored in .env as MODEL_ANTHROPIC)
def _get_anthropic_model() -> str:
    import os
    return os.environ.get("MODEL_ANTHROPIC", "claude-sonnet-4-20250514")

# System prompt for Claude — defines the RPG scribe role
SYSTEM_PROMPT = """You are a RPG session scribe.
Given the following session transcript, generate:
1. Session summary (narrative style, 2-3 paragraphs)
2. Key events timeline
3. Lore and world notes
4. Character moments
5. Cliffhangers and open threads"""


def summarize_session(session_dir: Path) -> Path:
    """
    Generate an AI-powered summary of a merged transcript.

    How it works:
    1. Reads the merged transcript from transcripts/merged.txt
    2. Sends it to Claude with the RPG scribe system prompt
    3. Claude generates a structured summary with 5 sections
    4. Saves the summary to session_dir/summary.md

    Args:
        session_dir: Path to the session directory.

    Returns:
        Path to the saved summary.md file.

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set.
        FileNotFoundError: If merged.txt doesn't exist.
    """
    session_dir = Path(session_dir)

    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Add it to your .env file.\n"
            "Get a key at: https://console.anthropic.com/settings/keys"
        )

    merged_path = session_dir / "transcripts" / "merged.txt"
    if not merged_path.exists():
        raise FileNotFoundError(
            f"Merged transcript not found at {merged_path}\n"
            "Run the merge step first."
        )

    # Read the merged transcript
    transcript = merged_path.read_text(encoding="utf-8")

    if not transcript.strip():
        print("Warning: Merged transcript is empty.")
        summary_path = session_dir / "summary.md"
        summary_path.write_text("# Session Summary\n\n*No transcript data available.*\n")
        return summary_path

    # Send to Claude
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    print("Sending transcript to Claude for summarization...")
    message = client.messages.create(
        model=_get_anthropic_model(),
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Here is the session transcript:\n\n{transcript}",
            }
        ],
    )

    # Extract the text response
    summary_text = message.content[0].text

    # Save as markdown
    summary_path = session_dir / "summary.md"
    summary_path.write_text(summary_text, encoding="utf-8")

    print(f"Summary saved to: {summary_path}")
    print(f"  Length: {len(summary_text)} characters")

    return summary_path


# --- Standalone test ---
if __name__ == "__main__":
    import sys
    from config import SESSIONS_DIR

    print("=== Summarizer Module Test ===\n")

    if not ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY not set in .env file.")
        print("Add your key to .env and try again.")
        print("Get a key at: https://console.anthropic.com/settings/keys")
        sys.exit(1)

    if not SESSIONS_DIR.exists():
        print(f"No sessions directory found at {SESSIONS_DIR}")
        print("Run the full pipeline first (record → process → transcribe → merge).")
        sys.exit(1)

    sessions = sorted(SESSIONS_DIR.iterdir())
    if not sessions:
        print("No session folders found.")
        sys.exit(1)

    latest = sessions[-1]
    print(f"Summarizing session: {latest.name}\n")

    summary_path = summarize_session(latest)

    # Show preview
    if summary_path.exists():
        content = summary_path.read_text(encoding="utf-8")
        print(f"\n--- Summary Preview ---")
        for line in content.splitlines()[:30]:
            print(f"  {line}")
        if len(content.splitlines()) > 30:
            print(f"  ... ({len(content.splitlines()) - 30} more lines)")
