"""Sessions API — list sessions, read transcripts and summaries."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()

_SESSIONS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "sessions"


@router.get("/")
async def list_sessions():
    """List all session directories with their available data."""
    if not _SESSIONS_DIR.exists():
        return []

    sessions = []
    for d in sorted(_SESSIONS_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        session = {
            "id": d.name,
            "has_transcript": (d / "transcripts" / "merged.txt").exists(),
            "has_summary": (d / "summary.md").exists(),
            "has_raw": any((d / "raw").glob("*")) if (d / "raw").exists() else False,
        }
        sessions.append(session)
    return sessions


@router.get("/{session_id}/transcript")
async def get_transcript(session_id: str):
    """Get the merged transcript for a session."""
    path = _SESSIONS_DIR / session_id / "transcripts" / "merged.txt"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {"session_id": session_id, "content": path.read_text(encoding="utf-8")}


@router.get("/{session_id}/summary")
async def get_summary(session_id: str):
    """Get the summary for a session."""
    path = _SESSIONS_DIR / session_id / "summary.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Summary not found")
    return {"session_id": session_id, "content": path.read_text(encoding="utf-8")}
