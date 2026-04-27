"""
Characters Page — SotDL character sheet management.

Left panel: character list with New/Delete buttons.
Right panel: full character sheet editor with tabbed sections:
  - Core: name, ancestry, level, paths, attributes
  - Combat: health, defense, speed, damage tracker
  - Abilities: talents, spells, equipment
  - Notes: corruption, insanity, fortune, freeform notes
"""

import json
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QScrollArea, QFrame, QLineEdit, QSpinBox,
    QComboBox, QTextEdit, QListWidget, QListWidgetItem,
    QTabWidget, QGridLayout, QCheckBox, QSplitter,
    QProgressBar, QMessageBox,
)
from PySide6.QtCore import Qt

from app.models.character import (
    Character, save_character, load_character, list_characters,
)

# Load SotDL game data (bundled read-only asset)
if getattr(sys, "frozen", False):
    _DATA_DIR = Path(sys._MEIPASS) / "data" / "sotdl"
else:
    _DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sotdl"
_GAME_DATA = {}
_game_data_file = _DATA_DIR / "game_data.json"
if _game_data_file.exists():
    _GAME_DATA = json.loads(_game_data_file.read_text(encoding="utf-8"))


class CharactersPage(QWidget):
    """Character sheet management — list + editor."""

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._current_char: Character | None = None
        self._current_path: Path | None = None
        self._loading = False  # prevent save-during-load loops
        self._stats_locked = True  # stats locked until Edit clicked
        self._lockable_widgets: list[QWidget] = []  # populated in _build_sheet
        self._build_ui()
        self._refresh_list()

    # ── UI Construction ─────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("🧙  Character Sheets")
        title.setObjectName("heading")
        layout.addWidget(title)

        # Splitter: list | sheet
        splitter = QSplitter(Qt.Horizontal)

        # ── Left: Character List ────────────────────────────────
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(8)

        list_label = QLabel("Characters")
        list_label.setObjectName("subheading")
        left_layout.addWidget(list_label)

        self._char_list = QListWidget()
        self._char_list.currentRowChanged.connect(self._on_char_selected)
        left_layout.addWidget(self._char_list, stretch=1)

        btn_row = QHBoxLayout()
        new_btn = QPushButton("✚ New")
        new_btn.setObjectName("primary")
        new_btn.clicked.connect(self._new_character)
        btn_row.addWidget(new_btn)

        del_btn = QPushButton("🗑 Delete")
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self._delete_character)
        btn_row.addWidget(del_btn)

        left_layout.addLayout(btn_row)

        left_panel.setMaximumWidth(220)
        splitter.addWidget(left_panel)

        # ── Right: Character Sheet ──────────────────────────────
        self._sheet_scroll = QScrollArea()
        self._sheet_scroll.setWidgetResizable(True)
        self._sheet_scroll.setFrameShape(QFrame.NoFrame)

        self._sheet_widget = QWidget()
        self._sheet_layout = QVBoxLayout(self._sheet_widget)
        self._sheet_layout.setContentsMargins(8, 0, 0, 0)
        self._sheet_layout.setSpacing(12)

        self._build_sheet()
        self._set_stats_locked(True)  # start locked

        self._sheet_scroll.setWidget(self._sheet_widget)
        splitter.addWidget(self._sheet_scroll)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, stretch=1)

    def _build_sheet(self):
        """Build the character sheet editor inside the right panel."""
        lay = self._sheet_layout

        # ── Identity Row ────────────────────────────────────────
        identity_group = QGroupBox("Identity")
        ig = QGridLayout(identity_group)
        ig.setSpacing(8)

        ig.addWidget(QLabel("Name:"), 0, 0)
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Character name")
        self._name_edit.textChanged.connect(self._auto_save)
        ig.addWidget(self._name_edit, 0, 1)

        ig.addWidget(QLabel("Level:"), 0, 2)
        self._level_spin = QSpinBox()
        self._level_spin.setRange(0, 10)
        self._level_spin.valueChanged.connect(self._auto_save)
        ig.addWidget(self._level_spin, 0, 3)

        ig.addWidget(QLabel("Ancestry:"), 1, 0)
        self._ancestry_combo = QComboBox()
        ancestries = [a["name"] for a in _GAME_DATA.get("ancestries", [])]
        self._ancestry_combo.addItems(ancestries or ["Human"])
        self._ancestry_combo.currentTextChanged.connect(self._on_ancestry_changed)
        ig.addWidget(self._ancestry_combo, 1, 1)

        ig.addWidget(QLabel("Size:"), 1, 2)
        self._size_edit = QLineEdit()
        self._size_edit.setFixedWidth(60)
        self._size_edit.textChanged.connect(self._auto_save)
        ig.addWidget(self._size_edit, 1, 3)

        ig.addWidget(QLabel("Novice Path:"), 2, 0)
        self._novice_combo = QComboBox()
        self._novice_combo.setEditable(True)
        novice = [p["name"] for p in _GAME_DATA.get("novice_paths", [])]
        self._novice_combo.addItems([""] + novice)
        self._novice_combo.currentTextChanged.connect(self._auto_save)
        ig.addWidget(self._novice_combo, 2, 1)

        ig.addWidget(QLabel("Expert Path:"), 2, 2)
        self._expert_combo = QComboBox()
        self._expert_combo.setEditable(True)
        self._expert_combo.addItems([""] + _GAME_DATA.get("expert_paths", []))
        self._expert_combo.currentTextChanged.connect(self._auto_save)
        ig.addWidget(self._expert_combo, 2, 3)

        ig.addWidget(QLabel("Master Path:"), 3, 0)
        self._master_combo = QComboBox()
        self._master_combo.setEditable(True)
        self._master_combo.addItems([""] + _GAME_DATA.get("master_paths", []))
        self._master_combo.currentTextChanged.connect(self._auto_save)
        ig.addWidget(self._master_combo, 3, 1)

        lay.addWidget(identity_group)

        # ── Edit / Lock Toggle ─────────────────────────────────
        self._edit_btn = QPushButton("🔓 Edit Stats")
        self._edit_btn.setObjectName("primary")
        self._edit_btn.setCheckable(True)
        self._edit_btn.setChecked(False)
        self._edit_btn.toggled.connect(self._toggle_stats_lock)
        lay.addWidget(self._edit_btn)

        # ── Attributes ──────────────────────────────────────────
        attr_group = QGroupBox("Attributes")
        ag = QGridLayout(attr_group)
        ag.setSpacing(8)

        self._attr_spins = {}
        attrs = [("Strength", "strength"), ("Agility", "agility"),
                 ("Intellect", "intellect"), ("Will", "will")]

        for col, (label, key) in enumerate(attrs):
            ag.addWidget(QLabel(label), 0, col * 2, 1, 2, Qt.AlignCenter)

            spin = QSpinBox()
            spin.setRange(1, 30)
            spin.setValue(10)
            spin.setFixedWidth(70)
            spin.valueChanged.connect(self._on_attr_changed)
            ag.addWidget(spin, 1, col * 2, 1, 2, Qt.AlignCenter)
            self._attr_spins[key] = spin

            mod_label = QLabel("(+0)")
            mod_label.setObjectName("muted")
            mod_label.setAlignment(Qt.AlignCenter)
            ag.addWidget(mod_label, 2, col * 2, 1, 2, Qt.AlignCenter)
            self._attr_spins[f"{key}_mod"] = mod_label

        lay.addWidget(attr_group)

        # ── Combat Stats ────────────────────────────────────────
        combat_group = QGroupBox("Combat")
        cg = QGridLayout(combat_group)
        cg.setSpacing(8)

        # Health bar
        cg.addWidget(QLabel("Health:"), 0, 0)
        self._health_bar = QProgressBar()
        self._health_bar.setTextVisible(True)
        self._health_bar.setFormat("%v / %m")
        cg.addWidget(self._health_bar, 0, 1, 1, 3)

        cg.addWidget(QLabel("Damage Taken:"), 1, 0)
        self._damage_spin = QSpinBox()
        self._damage_spin.setRange(0, 999)
        self._damage_spin.valueChanged.connect(self._on_damage_changed)
        cg.addWidget(self._damage_spin, 1, 1)

        cg.addWidget(QLabel("Health Bonus:"), 1, 2)
        self._health_bonus_spin = QSpinBox()
        self._health_bonus_spin.setRange(-50, 50)
        self._health_bonus_spin.valueChanged.connect(self._on_attr_changed)
        cg.addWidget(self._health_bonus_spin, 1, 3)

        # Defense, Speed, Healing Rate
        cg.addWidget(QLabel("Defense:"), 2, 0)
        self._defense_label = QLabel("10")
        self._defense_label.setObjectName("subheading")
        cg.addWidget(self._defense_label, 2, 1)

        cg.addWidget(QLabel("Defense Bonus:"), 2, 2)
        self._defense_bonus_spin = QSpinBox()
        self._defense_bonus_spin.setRange(-20, 30)
        self._defense_bonus_spin.valueChanged.connect(self._on_attr_changed)
        cg.addWidget(self._defense_bonus_spin, 2, 3)

        cg.addWidget(QLabel("Speed:"), 3, 0)
        self._speed_spin = QSpinBox()
        self._speed_spin.setRange(0, 30)
        self._speed_spin.setValue(10)
        self._speed_spin.valueChanged.connect(self._auto_save)
        cg.addWidget(self._speed_spin, 3, 1)

        cg.addWidget(QLabel("Healing Rate:"), 3, 2)
        self._healing_label = QLabel("—")
        self._healing_label.setObjectName("muted")
        cg.addWidget(self._healing_label, 3, 3)

        cg.addWidget(QLabel("Perception:"), 4, 0)
        self._perception_label = QLabel("+0")
        self._perception_label.setObjectName("subheading")
        cg.addWidget(self._perception_label, 4, 1)

        cg.addWidget(QLabel("Perception Bonus:"), 4, 2)
        self._perception_bonus_spin = QSpinBox()
        self._perception_bonus_spin.setRange(-10, 20)
        self._perception_bonus_spin.valueChanged.connect(self._on_attr_changed)
        cg.addWidget(self._perception_bonus_spin, 4, 3)

        lay.addWidget(combat_group)

        # ── Corruption & Insanity ───────────────────────────────
        dark_group = QGroupBox("Corruption & Insanity")
        dg = QGridLayout(dark_group)
        dg.setSpacing(8)

        dg.addWidget(QLabel("🩸 Corruption:"), 0, 0)
        self._corruption_spin = QSpinBox()
        self._corruption_spin.setRange(0, 20)
        self._corruption_spin.valueChanged.connect(self._auto_save)
        dg.addWidget(self._corruption_spin, 0, 1)

        dg.addWidget(QLabel("🌀 Insanity:"), 0, 2)
        self._insanity_spin = QSpinBox()
        self._insanity_spin.setRange(0, 20)
        self._insanity_spin.valueChanged.connect(self._auto_save)
        dg.addWidget(self._insanity_spin, 0, 3)

        dg.addWidget(QLabel("Power:"), 1, 0)
        self._power_spin = QSpinBox()
        self._power_spin.setRange(0, 10)
        self._power_spin.valueChanged.connect(self._auto_save)
        dg.addWidget(self._power_spin, 1, 1)

        self._fortune_check = QCheckBox("Fortune (reroll)")
        self._fortune_check.stateChanged.connect(self._auto_save)
        dg.addWidget(self._fortune_check, 1, 2, 1, 2)

        lay.addWidget(dark_group)

        # Register all lockable stat widgets
        self._lockable_widgets = [
            self._name_edit, self._level_spin, self._ancestry_combo,
            self._size_edit, self._novice_combo, self._expert_combo,
            self._master_combo,
            self._attr_spins["strength"], self._attr_spins["agility"],
            self._attr_spins["intellect"], self._attr_spins["will"],
            self._damage_spin, self._health_bonus_spin,
            self._defense_bonus_spin, self._speed_spin,
            self._perception_bonus_spin,
            self._corruption_spin, self._insanity_spin,
            self._power_spin, self._fortune_check,
        ]

        # ── Tabs: Talents / Spells / Equipment / Notes ──────────
        tabs = QTabWidget()

        # Talents tab
        talents_tab = QWidget()
        tl = QVBoxLayout(talents_tab)
        self._talents_edit = QTextEdit()
        self._talents_edit.setPlaceholderText("One talent per line...\ne.g. Weapon Training\nSurge of Strength")
        self._talents_edit.textChanged.connect(self._auto_save)
        tl.addWidget(self._talents_edit)
        tabs.addTab(talents_tab, "⚔️ Talents")

        # Spells tab
        spells_tab = QWidget()
        sl = QVBoxLayout(spells_tab)
        self._spells_edit = QTextEdit()
        self._spells_edit.setPlaceholderText(
            "Format: Tradition | Rank | Spell Name | Description\n"
            "e.g. Fire | 0 | Flame Missile | Ranged attack, 1d6 fire\n"
            "     Life | 1 | Minor Healing | Heal 1d6+Power"
        )
        self._spells_edit.textChanged.connect(self._auto_save)
        sl.addWidget(self._spells_edit)
        tabs.addTab(spells_tab, "✨ Spells")

        # Equipment tab
        equip_tab = QWidget()
        el = QVBoxLayout(equip_tab)
        self._equipment_edit = QTextEdit()
        self._equipment_edit.setPlaceholderText("One item per line...\ne.g. Longsword\nChain mail (Defense +4)\n10 gc")
        self._equipment_edit.textChanged.connect(self._auto_save)
        el.addWidget(self._equipment_edit)
        tabs.addTab(equip_tab, "🎒 Equipment")

        # Languages & Professions tab
        lang_tab = QWidget()
        ll = QVBoxLayout(lang_tab)
        ll.addWidget(QLabel("Languages (comma-separated):"))
        self._languages_edit = QLineEdit()
        self._languages_edit.textChanged.connect(self._auto_save)
        ll.addWidget(self._languages_edit)
        ll.addWidget(QLabel("Professions (comma-separated):"))
        self._professions_edit = QLineEdit()
        self._professions_edit.textChanged.connect(self._auto_save)
        ll.addWidget(self._professions_edit)
        ll.addStretch()
        tabs.addTab(lang_tab, "📖 Languages")

        # Notes tab
        notes_tab = QWidget()
        nl = QVBoxLayout(notes_tab)
        self._notes_edit = QTextEdit()
        self._notes_edit.setPlaceholderText("Backstory, session notes, anything else...")
        self._notes_edit.textChanged.connect(self._auto_save)
        nl.addWidget(self._notes_edit)
        tabs.addTab(notes_tab, "📝 Notes")

        lay.addWidget(tabs, stretch=1)

    # ── Character List ──────────────────────────────────────────

    def _refresh_list(self):
        self._char_list.clear()
        for name, path in list_characters():
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, str(path))
            self._char_list.addItem(item)

    def _on_char_selected(self, row: int):
        if row < 0:
            return
        item = self._char_list.item(row)
        path = Path(item.data(Qt.UserRole))
        if path.exists():
            self._current_char = load_character(path)
            self._current_path = path
            self._load_into_ui()

    def _new_character(self):
        char = Character(name="New Hero")
        path = save_character(char)
        self._refresh_list()
        # Select the new character
        for i in range(self._char_list.count()):
            if self._char_list.item(i).data(Qt.UserRole) == str(path):
                self._char_list.setCurrentRow(i)
                break

    def _delete_character(self):
        if not self._current_path or not self._current_path.exists():
            return
        reply = QMessageBox.question(
            self, "Delete Character",
            f"Delete '{self._current_char.name}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._current_path.unlink()
            self._current_char = None
            self._current_path = None
            self._refresh_list()

    # ── Load Character Into UI ──────────────────────────────────

    def _load_into_ui(self):
        """Populate all UI fields from self._current_char."""
        if not self._current_char:
            return
        c = self._current_char
        self._loading = True

        self._name_edit.setText(c.name)
        self._level_spin.setValue(c.level)
        self._size_edit.setText(c.size)

        # Ancestry combo
        idx = self._ancestry_combo.findText(c.ancestry)
        self._ancestry_combo.setCurrentIndex(max(0, idx))

        # Paths
        self._novice_combo.setCurrentText(c.novice_path)
        self._expert_combo.setCurrentText(c.expert_path)
        self._master_combo.setCurrentText(c.master_path)

        # Attributes
        self._attr_spins["strength"].setValue(c.strength)
        self._attr_spins["agility"].setValue(c.agility)
        self._attr_spins["intellect"].setValue(c.intellect)
        self._attr_spins["will"].setValue(c.will)

        # Combat
        self._health_bonus_spin.setValue(c.health_bonus)
        self._defense_bonus_spin.setValue(c.defense_bonus)
        self._speed_spin.setValue(c.speed_base)
        self._perception_bonus_spin.setValue(c.perception_bonus)
        self._damage_spin.setValue(c.damage_taken)

        # Dark
        self._corruption_spin.setValue(c.corruption)
        self._insanity_spin.setValue(c.insanity)
        self._power_spin.setValue(c.power)
        self._fortune_check.setChecked(c.fortune)

        # Lists
        self._talents_edit.setPlainText("\n".join(c.talents))
        self._equipment_edit.setPlainText("\n".join(c.equipment))
        self._languages_edit.setText(", ".join(c.languages))
        self._professions_edit.setText(", ".join(c.professions))
        self._notes_edit.setPlainText(c.notes)

        # Spells: format back to pipe-delimited
        spell_lines = []
        for sp in c.spells:
            line = f"{sp.get('tradition', '')} | {sp.get('rank', 0)} | {sp.get('name', '')} | {sp.get('description', '')}"
            spell_lines.append(line)
        self._spells_edit.setPlainText("\n".join(spell_lines))

        self._loading = False
        self._update_derived()

    # ── Save From UI ────────────────────────────────────────────

    def _auto_save(self):
        """Save current character whenever a field changes."""
        if self._loading or not self._current_char:
            return
        c = self._current_char

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

        # Parse spells
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
        if self._current_path:
            old_name = self._current_path.stem
            new_safe = "".join(ch if ch.isalnum() or ch in " _-" else "" for ch in c.name).strip() or "unnamed"
            if old_name != new_safe:
                new_path = self._current_path.parent / f"{new_safe}.json"
                if not new_path.exists() or new_path == self._current_path:
                    self._current_path.unlink(missing_ok=True)
                    self._current_path = new_path
                    # Update list item text
                    current = self._char_list.currentItem()
                    if current:
                        current.setText(c.name)
                        current.setData(Qt.UserRole, str(new_path))
            save_character(c, self._current_path.name)

    # ── Derived Stats ───────────────────────────────────────────

    def _update_derived(self):
        """Update all computed stat labels."""
        if not self._current_char:
            return
        c = self._current_char

        # Attribute modifiers
        for key in ("strength", "agility", "intellect", "will"):
            mod = getattr(c, f"{key}_mod")
            sign = "+" if mod >= 0 else ""
            self._attr_spins[f"{key}_mod"].setText(f"({sign}{mod})")

        # Health bar
        self._health_bar.setMaximum(max(1, c.health))
        self._health_bar.setValue(c.health_current)
        if c.is_incapacitated:
            self._health_bar.setStyleSheet("QProgressBar::chunk { background: #8b0000; }")
        elif c.is_injured:
            self._health_bar.setStyleSheet("QProgressBar::chunk { background: #c4a35a; }")
        else:
            self._health_bar.setStyleSheet("")

        # Defense
        self._defense_label.setText(str(c.defense))

        # Healing rate
        self._healing_label.setText(str(c.healing_rate))

        # Perception
        p = c.perception
        sign = "+" if p >= 0 else ""
        self._perception_label.setText(f"{sign}{p}")

    def _on_attr_changed(self):
        """When an attribute spinner changes, update derived stats and save."""
        self._auto_save()

    def _on_damage_changed(self):
        self._auto_save()

    # ── Stats Lock / Unlock ──────────────────────────────────

    def _set_stats_locked(self, locked: bool):
        """Enable or disable all stat widgets above the tabs."""
        self._stats_locked = locked
        for w in self._lockable_widgets:
            w.setEnabled(not locked)
        if locked:
            self._edit_btn.setText("🔓 Edit Stats")
        else:
            self._edit_btn.setText("🔒 Lock Stats")

    def _toggle_stats_lock(self, checked: bool):
        """Toggle button handler — checked means editing."""
        self._set_stats_locked(not checked)

    def _on_ancestry_changed(self, ancestry_name: str):
        """When ancestry changes, apply default attributes if creating new."""
        if self._loading:
            self._auto_save()
            return

        # Find ancestry data
        for a in _GAME_DATA.get("ancestries", []):
            if a["name"] == ancestry_name:
                self._size_edit.setText(a.get("size", "1"))
                self._speed_spin.setValue(a.get("speed", 10))
                break

        self._auto_save()
