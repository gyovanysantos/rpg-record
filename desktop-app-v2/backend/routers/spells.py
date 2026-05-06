"""Spells API — read-only access to the SotDL spell database."""

import json
from pathlib import Path
from fastapi import APIRouter, Query

router = APIRouter()

# Path to spells.json
_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "desktop-app" / "data" / "sotdl"
_SPELLS_FILE = _DATA_DIR / "spells.json"

_spells_cache: list[dict] | None = None


def _load_spells() -> list[dict]:
    global _spells_cache
    if _spells_cache is None:
        _spells_cache = json.loads(_SPELLS_FILE.read_text(encoding="utf-8"))
    return _spells_cache


@router.get("/")
async def get_spells(
    tradition: str | None = Query(None, description="Filter by tradition"),
    rank: int | None = Query(None, ge=0, le=10, description="Filter by rank"),
    search: str | None = Query(None, description="Search spell name or description"),
):
    """Get all spells, optionally filtered."""
    spells = _load_spells()

    if tradition:
        spells = [s for s in spells if s["tradition"].lower() == tradition.lower()]
    if rank is not None:
        spells = [s for s in spells if s["rank"] == rank]
    if search:
        q = search.lower()
        spells = [
            s for s in spells
            if q in s["name"].lower() or q in s.get("description", "").lower()
        ]

    return spells


@router.get("/traditions")
async def get_traditions():
    """Get list of all unique traditions."""
    spells = _load_spells()
    traditions = sorted(set(s["tradition"] for s in spells))
    return traditions
