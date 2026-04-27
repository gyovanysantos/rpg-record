"""
Character Sheet Dialog — opens as a separate window for editing a character.

Sections locked by default (Identity, Attributes, Combat, Corruption).
Bottom tabs (Talents, Spells, Equipment, Languages, Notes, Invocations) always editable.
"""

import json
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QScrollArea, QFrame, QLineEdit, QSpinBox,
    QComboBox, QTextEdit, QListWidget, QListWidgetItem,
    QTabWidget, QGridLayout, QCheckBox, QProgressBar,
    QMessageBox, QWidget, QSizePolicy, QFileDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon

import shutil

from app.models.character import Character, save_character, CHARACTERS_DIR

# Load SotDL game data (bundled read-only asset)
if getattr(sys, "frozen", False):
    _DATA_DIR = Path(sys._MEIPASS) / "data" / "sotdl"
else:
    _DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sotdl"
_GAME_DATA = {}
_game_data_file = _DATA_DIR / "game_data.json"
if _game_data_file.exists():
    _GAME_DATA = json.loads(_game_data_file.read_text(encoding="utf-8"))

# Pre-filled creature templates for invocations
_CREATURES: list[dict] = []
_creatures_file = _DATA_DIR / "creatures.json"
if _creatures_file.exists():
    _CREATURES = json.loads(_creatures_file.read_text(encoding="utf-8"))

# Pre-suggested hero portraits (bundled read-only)
if getattr(sys, "frozen", False):
    _PORTRAITS_DIR = Path(sys._MEIPASS) / "data" / "portraits"
else:
    _PORTRAITS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "portraits"

# User-uploaded portraits (writable, next to character files)
_USER_PORTRAITS_DIR = CHARACTERS_DIR.parent / "portraits"


# ── Invocation Editor Dialog ────────────────────────────────────

class InvocationEditorDialog(QDialog):
    """Separate window for editing a single invocation (creature stat block)."""

    def __init__(self, invocation: dict, parent=None):
        super().__init__(parent)
        self._inv = invocation
        self._loading = True

        self.setWindowTitle(f"Edit Invocation — {invocation.get('name', 'New')}")
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinMaxButtonsHint
            | Qt.WindowCloseButtonHint
        )
        self.setMinimumSize(700, 600)
        self.resize(800, 700)

        self._build_ui()
        self._load_data()
        self._loading = False

    def _build_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setSpacing(12)

        # Template selector at the top
        tmpl_row = QHBoxLayout()
        tmpl_row.addWidget(QLabel("Load Template:"))
        self._template_combo = QComboBox()
        self._template_combo.addItem("— Select template to pre-fill —")
        for c in _CREATURES:
            self._template_combo.addItem(f"{c['name']} (Dif. {c['difficulty']})")
        self._template_combo.currentIndexChanged.connect(self._apply_template)
        tmpl_row.addWidget(self._template_combo, stretch=1)
        main_lay.addLayout(tmpl_row)

        # Stat block form
        eg = QGridLayout()
        eg.setSpacing(10)

        row = 0
        eg.addWidget(QLabel("Name:"), row, 0)
        self._name = QLineEdit()
        self._name.setMinimumHeight(32)
        self._name.setPlaceholderText("Creature name")
        eg.addWidget(self._name, row, 1, 1, 5)

        row += 1
        eg.addWidget(QLabel("Difficulty:"), row, 0)
        self._difficulty = QSpinBox()
        self._difficulty.setRange(0, 999)
        self._difficulty.setMinimumHeight(32)
        eg.addWidget(self._difficulty, row, 1)

        eg.addWidget(QLabel("Type:"), row, 2)
        self._creature_type = QLineEdit()
        self._creature_type.setMinimumHeight(32)
        self._creature_type.setPlaceholderText("Animal, Monstro, etc.")
        eg.addWidget(self._creature_type, row, 3)

        eg.addWidget(QLabel("Size:"), row, 4)
        self._size = QLineEdit()
        self._size.setMinimumHeight(32)
        self._size.setMinimumWidth(60)
        self._size.setPlaceholderText("1/2, 1, 2...")
        eg.addWidget(self._size, row, 5)

        row += 1
        eg.addWidget(QLabel("Perception:"), row, 0)
        self._perception = QSpinBox()
        self._perception.setRange(0, 99)
        self._perception.setMinimumHeight(32)
        eg.addWidget(self._perception, row, 1)

        eg.addWidget(QLabel("Defense:"), row, 2)
        self._defense = QSpinBox()
        self._defense.setRange(0, 99)
        self._defense.setMinimumHeight(32)
        eg.addWidget(self._defense, row, 3)

        eg.addWidget(QLabel("Health:"), row, 4)
        self._health = QSpinBox()
        self._health.setRange(0, 999)
        self._health.setMinimumHeight(32)
        eg.addWidget(self._health, row, 5)

        row += 1
        eg.addWidget(QLabel("Strength:"), row, 0)
        self._strength = QSpinBox()
        self._strength.setRange(0, 99)
        self._strength.setMinimumHeight(32)
        eg.addWidget(self._strength, row, 1)

        eg.addWidget(QLabel("Agility:"), row, 2)
        self._agility = QSpinBox()
        self._agility.setRange(0, 99)
        self._agility.setMinimumHeight(32)
        eg.addWidget(self._agility, row, 3)

        row += 1
        eg.addWidget(QLabel("Intellect:"), row, 0)
        self._intellect = QSpinBox()
        self._intellect.setRange(0, 99)
        self._intellect.setMinimumHeight(32)
        eg.addWidget(self._intellect, row, 1)

        eg.addWidget(QLabel("Will:"), row, 2)
        self._will = QSpinBox()
        self._will.setRange(0, 99)
        self._will.setMinimumHeight(32)
        eg.addWidget(self._will, row, 3)

        eg.addWidget(QLabel("Speed:"), row, 4)
        self._speed = QSpinBox()
        self._speed.setRange(0, 99)
        self._speed.setMinimumHeight(32)
        eg.addWidget(self._speed, row, 5)

        row += 1
        eg.addWidget(QLabel("Traits:"), row, 0)
        self._traits = QLineEdit()
        self._traits.setMinimumHeight(32)
        self._traits.setPlaceholderText("e.g. visão no escuro")
        eg.addWidget(self._traits, row, 1, 1, 2)

        eg.addWidget(QLabel("Immunities:"), row, 3)
        self._immunities = QLineEdit()
        self._immunities.setMinimumHeight(32)
        self._immunities.setPlaceholderText("e.g. ganhar Insanidade")
        eg.addWidget(self._immunities, row, 4, 1, 2)

        row += 1
        eg.addWidget(QLabel("Attack Options:"), row, 0, Qt.AlignTop)
        self._attack_options = QTextEdit()
        self._attack_options.setMinimumHeight(80)
        self._attack_options.setPlaceholderText("e.g. Arma Natural (corpo a corpo) +5 com 1 dádiva (2d6)")
        eg.addWidget(self._attack_options, row, 1, 1, 5)

        row += 1
        eg.addWidget(QLabel("Special Attacks:"), row, 0, Qt.AlignTop)
        self._special_attacks = QTextEdit()
        self._special_attacks.setMinimumHeight(80)
        self._special_attacks.setPlaceholderText("e.g. Ataque Frenético, Ataque Massivo...")
        eg.addWidget(self._special_attacks, row, 1, 1, 5)

        row += 1
        eg.addWidget(QLabel("Description:"), row, 0, Qt.AlignTop)
        self._desc = QTextEdit()
        self._desc.setMinimumHeight(100)
        self._desc.setPlaceholderText("Creature description...")
        eg.addWidget(self._desc, row, 1, 1, 5)

        main_lay.addLayout(eg, stretch=1)

        # OK / Cancel buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("✔ Save")
        ok_btn.setObjectName("primary")
        ok_btn.setMinimumHeight(36)
        ok_btn.setMinimumWidth(120)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        main_lay.addLayout(btn_row)

    def _load_data(self):
        self._name.setText(self._inv.get("name", ""))
        self._difficulty.setValue(self._inv.get("difficulty", 0))
        self._creature_type.setText(self._inv.get("creature_type", ""))
        self._size.setText(str(self._inv.get("size", "1")))
        self._perception.setValue(self._inv.get("perception", 10))
        self._defense.setValue(self._inv.get("defense", 10))
        self._health.setValue(self._inv.get("health", 10))
        self._strength.setValue(self._inv.get("strength", 10))
        self._agility.setValue(self._inv.get("agility", 10))
        self._intellect.setValue(self._inv.get("intellect", 10))
        self._will.setValue(self._inv.get("will", 10))
        self._speed.setValue(self._inv.get("speed", 10))
        self._traits.setText(self._inv.get("traits", ""))
        self._immunities.setText(self._inv.get("immunities", ""))
        self._attack_options.setPlainText(self._inv.get("attack_options", ""))
        self._special_attacks.setPlainText(self._inv.get("special_attacks", ""))
        self._desc.setPlainText(self._inv.get("description", ""))

    def _apply_template(self, index: int):
        if self._loading or index <= 0:
            return
        template = _CREATURES[index - 1]
        self._name.setText(template.get("name", ""))
        self._difficulty.setValue(template.get("difficulty", 0))
        self._creature_type.setText(template.get("creature_type", ""))
        self._size.setText(str(template.get("size", "1")))
        self._perception.setValue(template.get("perception", 10))
        self._defense.setValue(template.get("defense", 10))
        self._health.setValue(template.get("health", 10))
        self._strength.setValue(template.get("strength", 10))
        self._agility.setValue(template.get("agility", 10))
        self._intellect.setValue(template.get("intellect", 10))
        self._will.setValue(template.get("will", 10))
        self._speed.setValue(template.get("speed", 10))
        self._traits.setText(template.get("traits", ""))
        self._immunities.setText(template.get("immunities", ""))
        self._attack_options.setPlainText(template.get("attack_options", ""))
        self._special_attacks.setPlainText(template.get("special_attacks", ""))
        self._desc.setPlainText(template.get("description", ""))
        self._template_combo.setCurrentIndex(0)

    def get_data(self) -> dict:
        """Return the edited invocation data."""
        return {
            "name": self._name.text(),
            "difficulty": self._difficulty.value(),
            "creature_type": self._creature_type.text(),
            "size": self._size.text(),
            "perception": self._perception.value(),
            "defense": self._defense.value(),
            "health": self._health.value(),
            "strength": self._strength.value(),
            "agility": self._agility.value(),
            "intellect": self._intellect.value(),
            "will": self._will.value(),
            "speed": self._speed.value(),
            "traits": self._traits.text(),
            "immunities": self._immunities.text(),
            "attack_options": self._attack_options.toPlainText(),
            "special_attacks": self._special_attacks.toPlainText(),
            "description": self._desc.toPlainText(),
        }


class CharacterSheetDialog(QDialog):
    """Full character sheet editor in its own window."""

    character_saved = Signal()  # emitted when the character is saved

    def __init__(self, character: Character, char_path: Path, parent=None):
        super().__init__(parent)
        self._char = character
        self._char_path = char_path
        self._loading = False
        self._stats_locked = True
        self._lockable_widgets: list[QWidget] = []

        self.setWindowTitle(f"Character Sheet — {character.name}")
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinMaxButtonsHint
            | Qt.WindowCloseButtonHint
        )
        self.setMinimumSize(800, 700)
        self.resize(900, 800)

        self._build_ui()
        self._load_into_ui()
        self._set_stats_locked(True)

    # ── UI Construction ─────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self._build_identity(lay)
        self._build_edit_button(lay)
        self._build_attributes(lay)
        self._build_combat(lay)
        self._build_dark(lay)
        self._register_lockable_widgets()
        self._build_tabs(lay)

        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

    # ── Identity ────────────────────────────────────────────────

    def _build_identity(self, lay: QVBoxLayout):
        group = QGroupBox("Identity")
        outer = QHBoxLayout(group)
        outer.setSpacing(16)

        # ── Left: Portrait square ───────────────────────────────
        portrait_panel = QVBoxLayout()
        portrait_panel.setSpacing(6)

        self._portrait_label = QLabel()
        self._portrait_label.setFixedSize(180, 260)
        self._portrait_label.setAlignment(Qt.AlignCenter)
        self._portrait_label.setStyleSheet(
            "QLabel { border: 2px solid #555; border-radius: 8px; background: #2a2a3a; }"
        )
        self._portrait_label.setScaledContents(False)
        portrait_panel.addWidget(self._portrait_label, alignment=Qt.AlignCenter)

        choose_btn = QPushButton("🖼 Choose Portrait")
        choose_btn.setMinimumHeight(28)
        choose_btn.clicked.connect(self._show_portrait_picker)
        portrait_panel.addWidget(choose_btn)

        upload_btn = QPushButton("📁 Upload Image")
        upload_btn.setMinimumHeight(28)
        upload_btn.clicked.connect(self._upload_portrait)
        portrait_panel.addWidget(upload_btn)

        portrait_panel.addStretch()
        outer.addLayout(portrait_panel)

        # ── Right: Identity fields ──────────────────────────────
        g = QGridLayout()
        g.setSpacing(10)

        g.addWidget(QLabel("Name:"), 0, 0)
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Character name")
        self._name_edit.setMinimumHeight(32)
        self._name_edit.textChanged.connect(self._auto_save)
        g.addWidget(self._name_edit, 0, 1)

        g.addWidget(QLabel("Level:"), 0, 2)
        self._level_spin = QSpinBox()
        self._level_spin.setRange(0, 10)
        self._level_spin.setMinimumHeight(32)
        self._level_spin.setMinimumWidth(80)
        self._level_spin.valueChanged.connect(self._auto_save)
        g.addWidget(self._level_spin, 0, 3)

        g.addWidget(QLabel("Ancestry:"), 1, 0)
        self._ancestry_combo = QComboBox()
        self._ancestry_combo.setEditable(True)
        self._ancestry_combo.setMinimumHeight(32)
        ancestries = [a["name"] for a in _GAME_DATA.get("ancestries", [])]
        self._ancestry_combo.addItems(ancestries or ["Human"])
        self._ancestry_combo.currentTextChanged.connect(self._on_ancestry_changed)
        g.addWidget(self._ancestry_combo, 1, 1)

        g.addWidget(QLabel("Size:"), 1, 2)
        self._size_edit = QLineEdit()
        self._size_edit.setFixedWidth(80)
        self._size_edit.setMinimumHeight(32)
        self._size_edit.textChanged.connect(self._auto_save)
        g.addWidget(self._size_edit, 1, 3)

        g.addWidget(QLabel("Novice Path:"), 2, 0)
        self._novice_combo = QComboBox()
        self._novice_combo.setEditable(True)
        self._novice_combo.setMinimumHeight(32)
        novice = [p["name"] for p in _GAME_DATA.get("novice_paths", [])]
        self._novice_combo.addItems([""] + novice)
        self._novice_combo.currentTextChanged.connect(self._auto_save)
        g.addWidget(self._novice_combo, 2, 1)

        g.addWidget(QLabel("Expert Path:"), 2, 2)
        self._expert_combo = QComboBox()
        self._expert_combo.setEditable(True)
        self._expert_combo.setMinimumHeight(32)
        self._expert_combo.addItems([""] + _GAME_DATA.get("expert_paths", []))
        self._expert_combo.currentTextChanged.connect(self._auto_save)
        g.addWidget(self._expert_combo, 2, 3)

        g.addWidget(QLabel("Master Path:"), 3, 0)
        self._master_combo = QComboBox()
        self._master_combo.setEditable(True)
        self._master_combo.setMinimumHeight(32)
        self._master_combo.addItems([""] + _GAME_DATA.get("master_paths", []))
        self._master_combo.currentTextChanged.connect(self._auto_save)
        g.addWidget(self._master_combo, 3, 1)

        outer.addLayout(g, stretch=1)
        lay.addWidget(group)

    # ── Edit / Lock Toggle ──────────────────────────────────────

    def _build_edit_button(self, lay: QVBoxLayout):
        self._edit_btn = QPushButton("🔓 Edit Stats")
        self._edit_btn.setObjectName("primary")
        self._edit_btn.setCheckable(True)
        self._edit_btn.setChecked(False)
        self._edit_btn.setMinimumHeight(36)
        self._edit_btn.toggled.connect(self._toggle_stats_lock)
        lay.addWidget(self._edit_btn)

    # ── Attributes ──────────────────────────────────────────────

    def _build_attributes(self, lay: QVBoxLayout):
        group = QGroupBox("Attributes")
        g = QGridLayout(group)
        g.setSpacing(10)

        self._attr_spins = {}
        attrs = [("Strength", "strength"), ("Agility", "agility"),
                 ("Intellect", "intellect"), ("Will", "will")]

        for col, (label, key) in enumerate(attrs):
            g.addWidget(QLabel(label), 0, col * 2, 1, 2, Qt.AlignCenter)

            spin = QSpinBox()
            spin.setRange(1, 30)
            spin.setValue(10)
            spin.setMinimumWidth(80)
            spin.setMinimumHeight(36)
            spin.valueChanged.connect(self._on_attr_changed)
            g.addWidget(spin, 1, col * 2, 1, 2, Qt.AlignCenter)
            self._attr_spins[key] = spin

            mod_label = QLabel("(+0)")
            mod_label.setObjectName("muted")
            mod_label.setAlignment(Qt.AlignCenter)
            g.addWidget(mod_label, 2, col * 2, 1, 2, Qt.AlignCenter)
            self._attr_spins[f"{key}_mod"] = mod_label

        lay.addWidget(group)

    # ── Combat Stats ────────────────────────────────────────────

    def _build_combat(self, lay: QVBoxLayout):
        group = QGroupBox("Combat")
        g = QGridLayout(group)
        g.setSpacing(10)

        # Health bar
        g.addWidget(QLabel("Health:"), 0, 0)
        self._health_bar = QProgressBar()
        self._health_bar.setTextVisible(True)
        self._health_bar.setFormat("%v / %m")
        self._health_bar.setMinimumHeight(28)
        g.addWidget(self._health_bar, 0, 1, 1, 3)

        g.addWidget(QLabel("Damage Taken:"), 1, 0)
        self._damage_spin = QSpinBox()
        self._damage_spin.setRange(0, 999)
        self._damage_spin.setMinimumHeight(32)
        self._damage_spin.setMinimumWidth(80)
        self._damage_spin.valueChanged.connect(self._on_damage_changed)
        g.addWidget(self._damage_spin, 1, 1)

        g.addWidget(QLabel("Health Bonus:"), 1, 2)
        self._health_bonus_spin = QSpinBox()
        self._health_bonus_spin.setRange(-50, 50)
        self._health_bonus_spin.setMinimumHeight(32)
        self._health_bonus_spin.setMinimumWidth(80)
        self._health_bonus_spin.valueChanged.connect(self._on_attr_changed)
        g.addWidget(self._health_bonus_spin, 1, 3)

        # Defense, Speed, Healing Rate
        g.addWidget(QLabel("Defense:"), 2, 0)
        self._defense_label = QLabel("10")
        self._defense_label.setObjectName("subheading")
        g.addWidget(self._defense_label, 2, 1)

        g.addWidget(QLabel("Defense Bonus:"), 2, 2)
        self._defense_bonus_spin = QSpinBox()
        self._defense_bonus_spin.setRange(-20, 30)
        self._defense_bonus_spin.setMinimumHeight(32)
        self._defense_bonus_spin.setMinimumWidth(80)
        self._defense_bonus_spin.valueChanged.connect(self._on_attr_changed)
        g.addWidget(self._defense_bonus_spin, 2, 3)

        g.addWidget(QLabel("Speed:"), 3, 0)
        self._speed_spin = QSpinBox()
        self._speed_spin.setRange(0, 30)
        self._speed_spin.setValue(10)
        self._speed_spin.setMinimumHeight(32)
        self._speed_spin.setMinimumWidth(80)
        self._speed_spin.valueChanged.connect(self._auto_save)
        g.addWidget(self._speed_spin, 3, 1)

        g.addWidget(QLabel("Healing Rate:"), 3, 2)
        self._healing_label = QLabel("—")
        self._healing_label.setObjectName("muted")
        g.addWidget(self._healing_label, 3, 3)

        g.addWidget(QLabel("Healing Rate Bonus:"), 4, 0)
        self._healing_rate_bonus_spin = QSpinBox()
        self._healing_rate_bonus_spin.setRange(-20, 50)
        self._healing_rate_bonus_spin.setMinimumHeight(32)
        self._healing_rate_bonus_spin.setMinimumWidth(80)
        self._healing_rate_bonus_spin.valueChanged.connect(self._on_attr_changed)
        g.addWidget(self._healing_rate_bonus_spin, 4, 1)

        g.addWidget(QLabel("Perception:"), 4, 2)
        self._perception_label = QLabel("+0")
        self._perception_label.setObjectName("subheading")
        g.addWidget(self._perception_label, 4, 3)

        g.addWidget(QLabel("Perception Bonus:"), 5, 0)
        self._perception_bonus_spin = QSpinBox()
        self._perception_bonus_spin.setRange(-10, 20)
        self._perception_bonus_spin.setMinimumHeight(32)
        self._perception_bonus_spin.setMinimumWidth(80)
        self._perception_bonus_spin.valueChanged.connect(self._on_attr_changed)
        g.addWidget(self._perception_bonus_spin, 5, 1)

        lay.addWidget(group)

    # ── Corruption & Insanity ───────────────────────────────────

    def _build_dark(self, lay: QVBoxLayout):
        group = QGroupBox("Corruption & Insanity")
        g = QGridLayout(group)
        g.setSpacing(10)

        g.addWidget(QLabel("🩸 Corruption:"), 0, 0)
        self._corruption_spin = QSpinBox()
        self._corruption_spin.setRange(0, 20)
        self._corruption_spin.setMinimumHeight(32)
        self._corruption_spin.setMinimumWidth(80)
        self._corruption_spin.valueChanged.connect(self._auto_save)
        g.addWidget(self._corruption_spin, 0, 1)

        g.addWidget(QLabel("🌀 Insanity:"), 0, 2)
        self._insanity_spin = QSpinBox()
        self._insanity_spin.setRange(0, 20)
        self._insanity_spin.setMinimumHeight(32)
        self._insanity_spin.setMinimumWidth(80)
        self._insanity_spin.valueChanged.connect(self._auto_save)
        g.addWidget(self._insanity_spin, 0, 3)

        g.addWidget(QLabel("Power:"), 1, 0)
        self._power_spin = QSpinBox()
        self._power_spin.setRange(0, 10)
        self._power_spin.setMinimumHeight(32)
        self._power_spin.setMinimumWidth(80)
        self._power_spin.valueChanged.connect(self._auto_save)
        g.addWidget(self._power_spin, 1, 1)

        self._fortune_check = QCheckBox("Fortune (reroll)")
        self._fortune_check.stateChanged.connect(self._auto_save)
        g.addWidget(self._fortune_check, 1, 2, 1, 2)

        lay.addWidget(group)

    # ── Register lockable widgets ───────────────────────────────

    def _register_lockable_widgets(self):
        self._lockable_widgets = [
            self._name_edit, self._level_spin, self._ancestry_combo,
            self._size_edit, self._novice_combo, self._expert_combo,
            self._master_combo,
            self._attr_spins["strength"], self._attr_spins["agility"],
            self._attr_spins["intellect"], self._attr_spins["will"],
            self._damage_spin, self._health_bonus_spin,
            self._healing_rate_bonus_spin,
            self._defense_bonus_spin, self._speed_spin,
            self._perception_bonus_spin,
            self._corruption_spin, self._insanity_spin,
            self._power_spin, self._fortune_check,
        ]

    # ── Tabs ────────────────────────────────────────────────────

    def _build_tabs(self, lay: QVBoxLayout):
        tabs = QTabWidget()

        # Talents
        t = QWidget()
        tl = QVBoxLayout(t)
        self._talents_edit = QTextEdit()
        self._talents_edit.setPlaceholderText("One talent per line...\ne.g. Weapon Training\nSurge of Strength")
        self._talents_edit.setMinimumHeight(120)
        self._talents_edit.textChanged.connect(self._auto_save)
        tl.addWidget(self._talents_edit)
        tabs.addTab(t, "⚔️ Talents")

        # Spells
        s = QWidget()
        sl = QVBoxLayout(s)
        self._spells_edit = QTextEdit()
        self._spells_edit.setPlaceholderText(
            "Format: Tradition | Rank | Spell Name | Description\n"
            "e.g. Fire | 0 | Flame Missile | Ranged attack, 1d6 fire"
        )
        self._spells_edit.setMinimumHeight(120)
        self._spells_edit.textChanged.connect(self._auto_save)
        sl.addWidget(self._spells_edit)
        tabs.addTab(s, "✨ Spells")

        # Equipment
        e = QWidget()
        el = QVBoxLayout(e)
        self._equipment_edit = QTextEdit()
        self._equipment_edit.setPlaceholderText("One item per line...\ne.g. Longsword\nChain mail (Defense +4)")
        self._equipment_edit.setMinimumHeight(120)
        self._equipment_edit.textChanged.connect(self._auto_save)
        el.addWidget(self._equipment_edit)
        tabs.addTab(e, "🎒 Equipment")

        # Languages & Professions
        lw = QWidget()
        ll = QVBoxLayout(lw)
        ll.addWidget(QLabel("Languages (comma-separated):"))
        self._languages_edit = QLineEdit()
        self._languages_edit.setMinimumHeight(32)
        self._languages_edit.textChanged.connect(self._auto_save)
        ll.addWidget(self._languages_edit)
        ll.addWidget(QLabel("Professions (comma-separated):"))
        self._professions_edit = QLineEdit()
        self._professions_edit.setMinimumHeight(32)
        self._professions_edit.textChanged.connect(self._auto_save)
        ll.addWidget(self._professions_edit)
        ll.addStretch()
        tabs.addTab(lw, "📖 Languages")

        # Notes
        n = QWidget()
        nl = QVBoxLayout(n)
        self._notes_edit = QTextEdit()
        self._notes_edit.setPlaceholderText("Backstory, session notes, anything else...")
        self._notes_edit.setMinimumHeight(120)
        self._notes_edit.textChanged.connect(self._auto_save)
        nl.addWidget(self._notes_edit)
        tabs.addTab(n, "📝 Notes")

        # Invocations
        inv = QWidget()
        inv_lay = QVBoxLayout(inv)
        self._build_invocations_tab(inv_lay)
        tabs.addTab(inv, "🔮 Invocations")

        lay.addWidget(tabs, stretch=1)

    # ── Invocations Tab ─────────────────────────────────────────

    def _build_invocations_tab(self, lay: QVBoxLayout):
        # Invocation list with summary info
        self._inv_list = QListWidget()
        self._inv_list.setMinimumHeight(150)
        self._inv_list.itemDoubleClicked.connect(self._edit_invocation)
        lay.addWidget(self._inv_list, stretch=1)

        # Buttons
        btn_row = QHBoxLayout()
        add_btn = QPushButton("✚ New")
        add_btn.setObjectName("primary")
        add_btn.setMinimumHeight(36)
        add_btn.clicked.connect(self._new_invocation)
        btn_row.addWidget(add_btn)

        edit_btn = QPushButton("✎ Edit")
        edit_btn.setMinimumHeight(36)
        edit_btn.clicked.connect(self._edit_invocation)
        btn_row.addWidget(edit_btn)

        del_btn = QPushButton("🗑 Delete")
        del_btn.setObjectName("danger")
        del_btn.setMinimumHeight(36)
        del_btn.clicked.connect(self._delete_invocation)
        btn_row.addWidget(del_btn)
        lay.addLayout(btn_row)

    def _refresh_inv_list(self):
        self._inv_list.clear()
        for inv in self._char.invocations:
            name = inv.get("name", "Unnamed")
            diff = inv.get("difficulty", 0)
            ctype = inv.get("creature_type", "")
            summary = f"{name}  —  Dif. {diff}  |  {ctype}" if ctype else f"{name}  —  Dif. {diff}"
            self._inv_list.addItem(summary)

    def _new_invocation(self):
        new_inv = {
            "name": "New Invocation",
            "difficulty": 0,
            "creature_type": "",
            "size": "1",
            "perception": 10,
            "defense": 10,
            "health": 10,
            "strength": 10,
            "agility": 10,
            "intellect": 10,
            "will": 10,
            "speed": 10,
            "traits": "",
            "immunities": "",
            "attack_options": "",
            "special_attacks": "",
            "description": "",
        }
        dlg = InvocationEditorDialog(new_inv, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._char.invocations.append(dlg.get_data())
            self._refresh_inv_list()
            self._auto_save()

    def _edit_invocation(self):
        row = self._inv_list.currentRow()
        if row < 0 or row >= len(self._char.invocations):
            return
        inv = self._char.invocations[row]
        dlg = InvocationEditorDialog(inv, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._char.invocations[row] = dlg.get_data()
            self._refresh_inv_list()
            self._auto_save()

    def _delete_invocation(self):
        row = self._inv_list.currentRow()
        if row < 0 or row >= len(self._char.invocations):
            return
        name = self._char.invocations[row].get("name", "Unnamed")
        reply = QMessageBox.question(
            self, "Delete Invocation",
            f"Delete '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._char.invocations.pop(row)
            self._refresh_inv_list()
            self._auto_save()

    # ── Portrait ──────────────────────────────────────────────────

    def _load_portrait(self):
        """Display the current portrait in the label."""
        portrait = self._char.portrait
        pixmap = None

        if portrait:
            # Check user-uploaded portraits first
            user_path = _USER_PORTRAITS_DIR / portrait
            if user_path.exists():
                pixmap = QPixmap(str(user_path))
            else:
                # Check bundled portraits
                bundled_path = _PORTRAITS_DIR / portrait
                if bundled_path.exists():
                    pixmap = QPixmap(str(bundled_path))

        if not pixmap or pixmap.isNull():
            default_path = _PORTRAITS_DIR / "default.png"
            if default_path.exists():
                pixmap = QPixmap(str(default_path))

        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                176, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self._portrait_label.setPixmap(scaled)

    def _show_portrait_picker(self):
        """Show a dialog with pre-suggested hero portraits to pick from."""
        from PySide6.QtWidgets import QDialog as _QDialog, QGridLayout as _QGrid

        picker = _QDialog(self)
        picker.setWindowTitle("Choose a Portrait")
        picker.setMinimumSize(700, 550)
        picker.resize(750, 600)

        picker_layout = QVBoxLayout(picker)
        picker_label = QLabel("Pick a full-body hero portrait:")
        picker_label.setObjectName("subheading")
        picker_layout.addWidget(picker_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        grid = _QGrid(scroll_widget)
        grid.setSpacing(12)

        portraits = sorted(_PORTRAITS_DIR.glob("*.png"))
        # Also include user-uploaded portraits
        if _USER_PORTRAITS_DIR.exists():
            portraits += sorted(_USER_PORTRAITS_DIR.glob("*.png"))
            portraits += sorted(_USER_PORTRAITS_DIR.glob("*.jpg"))
            portraits += sorted(_USER_PORTRAITS_DIR.glob("*.jpeg"))

        # Deduplicate by filename, prefer user version
        seen = {}
        for p in portraits:
            if p.name != "default.png":
                seen[p.name] = p
        portraits = list(seen.values())

        row, col = 0, 0
        max_cols = 4
        for img_path in portraits:
            px = QPixmap(str(img_path))
            if px.isNull():
                continue
            btn = QPushButton()
            btn.setFixedSize(150, 210)
            btn.setIcon(QIcon(px.scaled(140, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
            from PySide6.QtCore import QSize
            btn.setIconSize(QSize(140, 200))
            btn.setToolTip(img_path.stem.replace("_", " ").title())
            btn.setStyleSheet(
                "QPushButton { border: 2px solid #444; border-radius: 8px; background: #2a2a3a; padding: 4px; }"
                "QPushButton:hover { border-color: #c4a35a; border-width: 3px; }"
            )
            filename = img_path.name
            btn.clicked.connect(lambda checked, f=filename: self._select_portrait(f, picker))
            grid.addWidget(btn, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        scroll.setWidget(scroll_widget)
        picker_layout.addWidget(scroll, stretch=1)
        picker.exec()

    def _select_portrait(self, filename: str, picker_dialog):
        """Set the selected portrait and close the picker."""
        self._char.portrait = filename
        self._load_portrait()
        self._auto_save()
        picker_dialog.accept()

    def _upload_portrait(self):
        """Let the user pick an image file and copy it to the user portraits folder."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Upload Portrait Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not file_path:
            return
        src = Path(file_path)
        _USER_PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)

        # Use a safe filename based on character name + original extension
        safe_name = "".join(
            ch if ch.isalnum() or ch in " _-" else "" for ch in self._char.name
        ).strip() or "custom"
        dest_name = f"{safe_name}{src.suffix.lower()}"
        dest = _USER_PORTRAITS_DIR / dest_name

        shutil.copy2(str(src), str(dest))
        self._char.portrait = dest_name
        self._load_portrait()
        self._auto_save()

    # ── Stats Lock / Unlock ─────────────────────────────────────

    def _set_stats_locked(self, locked: bool):
        self._stats_locked = locked
        for w in self._lockable_widgets:
            w.setEnabled(not locked)
        self._edit_btn.setText("🔓 Edit Stats" if locked else "🔒 Lock Stats")

    def _toggle_stats_lock(self, checked: bool):
        self._set_stats_locked(not checked)

    # ── Load Character Into UI ──────────────────────────────────

    def _load_into_ui(self):
        if not self._char:
            return
        c = self._char
        self._loading = True

        self._name_edit.setText(c.name)
        self._level_spin.setValue(c.level)
        self._size_edit.setText(c.size)

        idx = self._ancestry_combo.findText(c.ancestry)
        if idx >= 0:
            self._ancestry_combo.setCurrentIndex(idx)
        else:
            self._ancestry_combo.setCurrentText(c.ancestry)

        self._novice_combo.setCurrentText(c.novice_path)
        self._expert_combo.setCurrentText(c.expert_path)
        self._master_combo.setCurrentText(c.master_path)

        self._attr_spins["strength"].setValue(c.strength)
        self._attr_spins["agility"].setValue(c.agility)
        self._attr_spins["intellect"].setValue(c.intellect)
        self._attr_spins["will"].setValue(c.will)

        self._health_bonus_spin.setValue(c.health_bonus)
        self._healing_rate_bonus_spin.setValue(c.healing_rate_bonus)
        self._defense_bonus_spin.setValue(c.defense_bonus)
        self._speed_spin.setValue(c.speed_base)
        self._perception_bonus_spin.setValue(c.perception_bonus)
        self._damage_spin.setValue(c.damage_taken)

        self._corruption_spin.setValue(c.corruption)
        self._insanity_spin.setValue(c.insanity)
        self._power_spin.setValue(c.power)
        self._fortune_check.setChecked(c.fortune)

        self._talents_edit.setPlainText("\n".join(c.talents))
        self._equipment_edit.setPlainText("\n".join(c.equipment))
        self._languages_edit.setText(", ".join(c.languages))
        self._professions_edit.setText(", ".join(c.professions))
        self._notes_edit.setPlainText(c.notes)

        spell_lines = []
        for sp in c.spells:
            line = f"{sp.get('tradition', '')} | {sp.get('rank', 0)} | {sp.get('name', '')} | {sp.get('description', '')}"
            spell_lines.append(line)
        self._spells_edit.setPlainText("\n".join(spell_lines))

        self._refresh_inv_list()
        self._load_portrait()

        self._loading = False
        self._update_derived()

    # ── Save From UI ────────────────────────────────────────────

    def _auto_save(self):
        if self._loading or not self._char:
            return
        c = self._char

        c.name = self._name_edit.text()
        c.level = self._level_spin.value()
        c.ancestry = self._ancestry_combo.currentText()
        c.size = self._size_edit.text()
        c.novice_path = self._novice_combo.currentText()
        c.expert_path = self._expert_combo.currentText()
        c.master_path = self._master_combo.currentText()

        c.strength = self._attr_spins["strength"].value()
        c.agility = self._attr_spins["agility"].value()
        c.intellect = self._attr_spins["intellect"].value()
        c.will = self._attr_spins["will"].value()

        c.health_bonus = self._health_bonus_spin.value()
        c.healing_rate_bonus = self._healing_rate_bonus_spin.value()
        c.defense_bonus = self._defense_bonus_spin.value()
        c.speed_base = self._speed_spin.value()
        c.perception_bonus = self._perception_bonus_spin.value()
        c.damage_taken = self._damage_spin.value()

        c.corruption = self._corruption_spin.value()
        c.insanity = self._insanity_spin.value()
        c.power = self._power_spin.value()
        c.fortune = self._fortune_check.isChecked()

        c.talents = [t for t in self._talents_edit.toPlainText().splitlines() if t.strip()]
        c.equipment = [e for e in self._equipment_edit.toPlainText().splitlines() if e.strip()]
        c.languages = [l.strip() for l in self._languages_edit.text().split(",") if l.strip()]
        c.professions = [p.strip() for p in self._professions_edit.text().split(",") if p.strip()]
        c.notes = self._notes_edit.toPlainText()

        spells = []
        for line in self._spells_edit.toPlainText().splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                spells.append({
                    "tradition": parts[0],
                    "rank": int(parts[1]) if parts[1].isdigit() else 0,
                    "name": parts[2],
                    "description": parts[3] if len(parts) > 3 else "",
                })
        c.spells = spells

        self._update_derived()

        # Save to file (rename if name changed)
        if self._char_path:
            old_name = self._char_path.stem
            new_safe = "".join(ch if ch.isalnum() or ch in " _-" else "" for ch in c.name).strip() or "unnamed"
            if old_name != new_safe:
                new_path = self._char_path.parent / f"{new_safe}.json"
                if not new_path.exists() or new_path == self._char_path:
                    self._char_path.unlink(missing_ok=True)
                    self._char_path = new_path
            save_character(c, self._char_path.name)
            self.setWindowTitle(f"Character Sheet — {c.name}")
            self.character_saved.emit()

    # ── Derived Stats ───────────────────────────────────────────

    def _update_derived(self):
        if not self._char:
            return
        c = self._char

        for key in ("strength", "agility", "intellect", "will"):
            mod = getattr(c, f"{key}_mod")
            sign = "+" if mod >= 0 else ""
            self._attr_spins[f"{key}_mod"].setText(f"({sign}{mod})")

        self._health_bar.setMaximum(max(1, c.health))
        self._health_bar.setValue(c.health_current)
        if c.is_incapacitated:
            self._health_bar.setStyleSheet("QProgressBar::chunk { background: #8b0000; }")
        elif c.is_injured:
            self._health_bar.setStyleSheet("QProgressBar::chunk { background: #c4a35a; }")
        else:
            self._health_bar.setStyleSheet("")

        self._defense_label.setText(str(c.defense))
        self._healing_label.setText(str(c.healing_rate))

        p = c.perception
        sign = "+" if p >= 0 else ""
        self._perception_label.setText(f"{sign}{p}")

    def _on_attr_changed(self):
        self._auto_save()

    def _on_damage_changed(self):
        self._auto_save()

    def _on_ancestry_changed(self, ancestry_name: str):
        if self._loading:
            self._auto_save()
            return
        for a in _GAME_DATA.get("ancestries", []):
            if a["name"] == ancestry_name:
                self._size_edit.setText(a.get("size", "1"))
                self._speed_spin.setValue(a.get("speed", 10))
                break
        self._auto_save()
