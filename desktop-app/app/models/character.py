"""
Shadow of the Demon Lord — Character data model.

Covers the full SotDL character sheet:
- 4 core attributes (Str, Agi, Int, Will) — modifier = score - 10
- Derived stats: Health, Healing Rate, Defense, Speed, Size, Power, Damage, Insanity, Corruption
- Ancestry (race), Level 0-10
- Novice/Expert/Master paths
- Talents, Spells, Equipment, Languages
- Corruption & Insanity tracking
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

CHARACTERS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "characters"


@dataclass
class Character:
    """A Shadow of the Demon Lord player character."""

    # ── Identity ────────────────────────────────────────────────
    name: str = "New Character"
    ancestry: str = "Human"
    level: int = 0
    novice_path: str = ""
    expert_path: str = ""
    master_path: str = ""

    # ── Core Attributes (base scores) ──────────────────────────
    strength: int = 10
    agility: int = 10
    intellect: int = 10
    will: int = 10

    # ── Derived / Overrideable Stats ───────────────────────────
    health_bonus: int = 0      # extra HP from paths/talents
    defense_bonus: int = 0     # armor/shield/talent bonuses
    speed_base: int = 10
    size: str = "1"            # 1 for most, 1/2 for small, 2 for large
    perception_bonus: int = 0
    power: int = 0             # spellcasting power

    # ── Damage & Conditions ────────────────────────────────────
    damage_taken: int = 0
    insanity: int = 0
    corruption: int = 0

    # ── Fortune ────────────────────────────────────────────────
    fortune: bool = True       # reroll once per session

    # ── Lists ──────────────────────────────────────────────────
    languages: list[str] = field(default_factory=lambda: ["Common"])
    professions: list[str] = field(default_factory=list)
    talents: list[str] = field(default_factory=list)
    spells: list[dict] = field(default_factory=list)  # {"name", "tradition", "rank", "description"}
    equipment: list[str] = field(default_factory=list)
    notes: str = ""

    # ── Computed Properties ─────────────────────────────────────

    @property
    def strength_mod(self) -> int:
        return self.strength - 10

    @property
    def agility_mod(self) -> int:
        return self.agility - 10

    @property
    def intellect_mod(self) -> int:
        return self.intellect - 10

    @property
    def will_mod(self) -> int:
        return self.will - 10

    @property
    def health(self) -> int:
        return self.strength + self.health_bonus

    @property
    def healing_rate(self) -> int:
        return max(1, self.health // 4)

    @property
    def defense(self) -> int:
        return self.agility + self.defense_bonus

    @property
    def perception(self) -> int:
        return self.intellect_mod + self.perception_bonus

    @property
    def health_current(self) -> int:
        return max(0, self.health - self.damage_taken)

    @property
    def is_injured(self) -> bool:
        return self.damage_taken >= self.health // 2

    @property
    def is_incapacitated(self) -> bool:
        return self.damage_taken >= self.health

    # ── Serialization ───────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ancestry": self.ancestry,
            "level": self.level,
            "novice_path": self.novice_path,
            "expert_path": self.expert_path,
            "master_path": self.master_path,
            "strength": self.strength,
            "agility": self.agility,
            "intellect": self.intellect,
            "will": self.will,
            "health_bonus": self.health_bonus,
            "defense_bonus": self.defense_bonus,
            "speed_base": self.speed_base,
            "size": self.size,
            "perception_bonus": self.perception_bonus,
            "power": self.power,
            "damage_taken": self.damage_taken,
            "insanity": self.insanity,
            "corruption": self.corruption,
            "fortune": self.fortune,
            "languages": self.languages,
            "professions": self.professions,
            "talents": self.talents,
            "spells": self.spells,
            "equipment": self.equipment,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def save_character(char: Character, filename: str | None = None) -> Path:
    """Save a character to JSON in data/characters/."""
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    if not filename:
        safe = "".join(c if c.isalnum() or c in " _-" else "" for c in char.name).strip()
        filename = f"{safe or 'unnamed'}.json"
    path = CHARACTERS_DIR / filename
    path.write_text(json.dumps(char.to_dict(), indent=2), encoding="utf-8")
    return path


def load_character(path: Path) -> Character:
    """Load a character from a JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return Character.from_dict(data)


def list_characters() -> list[tuple[str, Path]]:
    """Return (name, path) for all saved characters."""
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    chars = []
    for f in CHARACTERS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            chars.append((data.get("name", f.stem), f))
        except Exception:
            chars.append((f.stem, f))
    return sorted(chars, key=lambda x: x[0].lower())
