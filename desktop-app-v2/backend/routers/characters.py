"""Characters CRUD API — wraps existing character.py model."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.character import (
    Character,
    save_character,
    load_character,
    list_characters,
    CHARACTERS_DIR,
)

router = APIRouter()


class CharacterData(BaseModel):
    """Request body for creating/updating a character."""
    name: str = "New Character"
    ancestry: str = "Human"
    level: int = 0
    novice_path: str = ""
    expert_path: str = ""
    master_path: str = ""
    strength: int = 10
    agility: int = 10
    intellect: int = 10
    will: int = 10
    health_bonus: int = 0
    healing_rate_bonus: int = 0
    defense_bonus: int = 0
    speed_base: int = 10
    size: str = "1"
    perception_bonus: int = 0
    power: int = 0
    damage_taken: int = 0
    insanity: int = 0
    corruption: int = 0
    fortune: bool = True
    languages: list[str] = ["Common"]
    professions: list[str] = []
    talents: list[dict] = []
    spells: list[dict] = []
    equipment: list[dict] = []
    invocations: list[dict] = []
    gold: int = 0
    notes: str = ""
    portrait: str = ""


@router.get("/")
async def get_characters():
    """List all saved characters."""
    chars = list_characters()
    return [{"name": name, "filename": path.name} for name, path in chars]


@router.get("/{filename}")
async def get_character(filename: str):
    """Load a specific character by filename."""
    path = CHARACTERS_DIR / filename
    if not path.exists() or not path.suffix == ".json":
        raise HTTPException(status_code=404, detail="Character not found")
    char = load_character(path)
    data = char.to_dict()
    # Include computed properties
    data["health"] = char.health
    data["healing_rate"] = char.healing_rate
    data["defense"] = char.defense
    data["perception"] = char.perception
    data["health_current"] = char.health_current
    data["is_injured"] = char.is_injured
    data["is_incapacitated"] = char.is_incapacitated
    data["filename"] = filename
    return data


@router.post("/")
async def create_character(data: CharacterData):
    """Create a new character."""
    char = Character.from_dict(data.model_dump())
    path = save_character(char)
    return {"filename": path.name, "name": char.name}


@router.put("/{filename}")
async def update_character(filename: str, data: CharacterData):
    """Update an existing character."""
    path = CHARACTERS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Character not found")
    char = Character.from_dict(data.model_dump())
    save_character(char, filename)
    return {"filename": filename, "name": char.name}


@router.delete("/{filename}")
async def delete_character(filename: str):
    """Delete a character."""
    path = CHARACTERS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Character not found")
    path.unlink()
    return {"deleted": filename}
