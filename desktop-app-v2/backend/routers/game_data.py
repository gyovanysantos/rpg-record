"""Game Data API — ancestries, paths, traditions from game_data.json + creatures."""

import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

_SOTDL_DIR = Path(__file__).resolve().parent.parent.parent.parent / "desktop-app" / "data" / "sotdl"
_DATA_FILE = _SOTDL_DIR / "game_data.json"
_CREATURES_FILE = _SOTDL_DIR / "creatures.json"
_cache: dict | None = None
_creatures_cache: list | None = None


def _load() -> dict:
    global _cache
    if _cache is None:
        _cache = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    return _cache


def _load_creatures() -> list:
    global _creatures_cache
    if _creatures_cache is None:
        _creatures_cache = json.loads(_CREATURES_FILE.read_text(encoding="utf-8"))
    return _creatures_cache


@router.get("/ancestries")
async def get_ancestries():
    return _load()["ancestries"]


@router.get("/paths/novice")
async def get_novice_paths():
    return _load()["novice_paths"]


@router.get("/paths/expert")
async def get_expert_paths():
    return _load()["expert_paths"]


@router.get("/paths/master")
async def get_master_paths():
    return _load()["master_paths"]


@router.get("/traditions")
async def get_traditions():
    return _load()["spell_traditions"]


@router.get("/creatures")
async def get_creatures():
    """Return creature templates for invocations."""
    return _load_creatures()
