"""
Campaign & Session data models.

Campaigns are named folders under data/campaigns/.
Sessions live in the repo-root sessions/ directory.
This module scans both to build the dashboard view.
"""

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# When frozen (.exe), store user data next to the executable so it persists.
# When running from source, use the normal directory layout.
if getattr(sys, "frozen", False):
    _APP_DIR = Path(sys.executable).resolve().parent
    _REPO_ROOT = _APP_DIR
else:
    _APP_DIR = Path(__file__).resolve().parent.parent.parent
    _REPO_ROOT = _APP_DIR.parent
SESSIONS_DIR = _REPO_ROOT / "sessions"
CAMPAIGNS_DIR = _APP_DIR / "data" / "campaigns"


@dataclass
class SessionInfo:
    """Metadata for a single recording session."""
    path: Path
    name: str                    # folder name, e.g. "2026-04-25_2"
    date: datetime | None        # parsed from folder name
    has_raw: bool = False
    has_processed: bool = False
    has_transcript: bool = False
    has_merged: bool = False
    has_summary: bool = False
    raw_file_count: int = 0
    transcript_preview: str = ""
    summary_preview: str = ""

    @property
    def status(self) -> str:
        if self.has_summary:
            return "Summarized"
        if self.has_merged:
            return "Merged"
        if self.has_transcript:
            return "Transcribed"
        if self.has_processed:
            return "Processed"
        if self.has_raw:
            return "Recorded"
        return "Empty"

    @property
    def status_icon(self) -> str:
        icons = {
            "Summarized": "✅",
            "Merged": "📝",
            "Transcribed": "📋",
            "Processed": "⚙️",
            "Recorded": "🎙️",
            "Empty": "📂",
        }
        return icons.get(self.status, "📂")


@dataclass
class Campaign:
    """A named campaign that groups sessions."""
    name: str
    path: Path
    created: datetime | None = None
    description: str = ""
    session_ids: list[str] = field(default_factory=list)


def scan_session(session_path: Path) -> SessionInfo:
    """Build a SessionInfo from a session directory."""
    name = session_path.name

    # Parse date from folder name (e.g. "2026-04-25" or "2026-04-25_2")
    date_str = name.split("_")[0] if "_" in name else name
    # Handle names like "2026-04-25_2" → date part is "2026-04-25"
    # But also "2026-04-25" with no suffix
    try:
        # Try parsing just the date portion
        parts = name.split("_")
        if len(parts) >= 3:
            # "2026-04-25" splits to ["2026", "04", "25"]
            # "2026-04-25_2" splits to ["2026", "04", "25", "2"]
            date_str = f"{parts[0]}-{parts[1]}-{parts[2][:2]}"
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, IndexError):
        parsed_date = None

    raw_dir = session_path / "raw"
    processed_dir = session_path / "processed"
    transcripts_dir = session_path / "transcripts"

    raw_files = list(raw_dir.glob("*.wav")) if raw_dir.exists() else []
    processed_files = list(processed_dir.glob("*.wav")) if processed_dir.exists() else []
    transcript_files = list(transcripts_dir.glob("*.json")) if transcripts_dir.exists() else []
    merged_file = transcripts_dir / "merged.txt"
    summary_file = session_path / "summary.md"

    # Get transcript preview
    preview = ""
    if merged_file.exists():
        try:
            lines = merged_file.read_text(encoding="utf-8").strip().splitlines()
            preview = "\n".join(lines[:3])
            if len(lines) > 3:
                preview += f"\n... ({len(lines)} lines total)"
        except Exception:
            pass

    # Get summary preview
    summary_preview = ""
    if summary_file.exists():
        try:
            text = summary_file.read_text(encoding="utf-8").strip()
            summary_preview = text[:200] + "..." if len(text) > 200 else text
        except Exception:
            pass

    return SessionInfo(
        path=session_path,
        name=name,
        date=parsed_date,
        has_raw=len(raw_files) > 0,
        has_processed=len(processed_files) > 0,
        has_transcript=len(transcript_files) > 0,
        has_merged=merged_file.exists(),
        has_summary=summary_file.exists(),
        raw_file_count=len(raw_files),
        transcript_preview=preview,
        summary_preview=summary_preview,
    )


def scan_all_sessions() -> list[SessionInfo]:
    """Scan the sessions/ directory and return info for each session, newest first."""
    if not SESSIONS_DIR.exists():
        return []

    sessions = []
    for entry in SESSIONS_DIR.iterdir():
        if entry.is_dir():
            sessions.append(scan_session(entry))

    # Sort by date descending (newest first), None dates last
    sessions.sort(
        key=lambda s: s.date or datetime.min,
        reverse=True,
    )
    return sessions


def load_campaigns() -> list[Campaign]:
    """Load all campaigns from data/campaigns/."""
    CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)
    campaigns = []

    for entry in CAMPAIGNS_DIR.iterdir():
        if entry.is_dir():
            meta_file = entry / "campaign.json"
            if meta_file.exists():
                try:
                    data = json.loads(meta_file.read_text(encoding="utf-8"))
                    campaigns.append(Campaign(
                        name=data.get("name", entry.name),
                        path=entry,
                        description=data.get("description", ""),
                        session_ids=data.get("sessions", []),
                    ))
                except Exception:
                    campaigns.append(Campaign(name=entry.name, path=entry))
            else:
                campaigns.append(Campaign(name=entry.name, path=entry))

    return campaigns


def create_campaign(name: str, description: str = "") -> Campaign:
    """Create a new campaign folder with metadata."""
    CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)

    # Sanitize folder name
    safe_name = "".join(c if c.isalnum() or c in " _-" else "" for c in name).strip()
    if not safe_name:
        safe_name = "unnamed"

    campaign_dir = CAMPAIGNS_DIR / safe_name
    campaign_dir.mkdir(exist_ok=True)

    meta = {
        "name": name,
        "description": description,
        "created": datetime.now().isoformat(),
        "sessions": [],
    }
    (campaign_dir / "campaign.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    return Campaign(
        name=name,
        path=campaign_dir,
        description=description,
        created=datetime.now(),
    )
