"""
Initiative Tracker — SotDL Fast/Slow turn system.

SotDL Initiative:
- Each round, combatants choose FAST or SLOW turn
- FAST turn: take ONE action (move OR action, not both), goes first
- SLOW turn: take TWO actions (move AND action), goes after all fast turns
- Within fast/slow groups, PCs go before NPCs (or GM decides)
- No initiative roll — purely tactical choice

Features:
- Add PCs and NPCs/Monsters with names
- Toggle fast/slow per combatant per round
- Visual grouping: Fast PCs → Fast NPCs → Slow PCs → Slow NPCs
- Round counter
- HP tracking per combatant
- Conditions/notes per combatant
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QLineEdit, QSpinBox, QGridLayout, QScrollArea,
    QFrame, QCheckBox, QMessageBox, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class Combatant:
    """A single combatant in the initiative tracker."""

    def __init__(self, name: str, is_pc: bool = True, hp_max: int = 0):
        self.name = name
        self.is_pc = is_pc
        self.hp_max = hp_max
        self.hp_current = hp_max
        self.is_fast = False  # slow by default
        self.acted = False
        self.notes = ""

    @property
    def type_label(self) -> str:
        return "PC" if self.is_pc else "NPC"


class CombatantCard(QFrame):
    """Visual card for a single combatant in the tracker."""

    removed = Signal(object)
    changed = Signal()

    def __init__(self, combatant: Combatant, parent=None):
        super().__init__(parent)
        self.combatant = combatant
        self.setObjectName("card")
        self.setFrameShape(QFrame.StyledPanel)
        self._build_ui()
        self._update_style()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Acted checkbox
        self._acted_check = QCheckBox()
        self._acted_check.setToolTip("Mark as acted")
        self._acted_check.setChecked(self.combatant.acted)
        self._acted_check.stateChanged.connect(self._on_acted)
        layout.addWidget(self._acted_check)

        # Name + type
        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)

        self._name_label = QLabel(self.combatant.name)
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        self._name_label.setFont(font)
        name_layout.addWidget(self._name_label)

        type_label = QLabel(self.combatant.type_label)
        type_label.setObjectName("muted")
        type_label.setStyleSheet("font-size: 11px;")
        name_layout.addWidget(type_label)

        layout.addLayout(name_layout)
        layout.addStretch()

        # Fast/Slow toggle
        self._fast_btn = QPushButton("⚡ FAST")
        self._fast_btn.setCheckable(True)
        self._fast_btn.setChecked(self.combatant.is_fast)
        self._fast_btn.setFixedWidth(90)
        self._fast_btn.setFixedHeight(32)
        self._fast_btn.toggled.connect(self._on_fast_toggle)
        self._update_fast_btn()
        layout.addWidget(self._fast_btn)

        # HP
        if self.combatant.hp_max > 0:
            hp_layout = QVBoxLayout()
            hp_layout.setSpacing(2)
            hp_lbl = QLabel("HP")
            hp_lbl.setObjectName("muted")
            hp_lbl.setAlignment(Qt.AlignCenter)
            hp_layout.addWidget(hp_lbl)

            self._hp_spin = QSpinBox()
            self._hp_spin.setRange(0, 999)
            self._hp_spin.setValue(self.combatant.hp_current)
            self._hp_spin.setFixedWidth(70)
            self._hp_spin.valueChanged.connect(self._on_hp_changed)
            hp_layout.addWidget(self._hp_spin)

            layout.addLayout(hp_layout)

        # Notes
        self._notes_edit = QLineEdit()
        self._notes_edit.setPlaceholderText("notes...")
        self._notes_edit.setFixedWidth(140)
        self._notes_edit.setText(self.combatant.notes)
        self._notes_edit.textChanged.connect(self._on_notes_changed)
        layout.addWidget(self._notes_edit)

        # Remove button
        remove_btn = QPushButton("✕")
        remove_btn.setObjectName("danger")
        remove_btn.setFixedSize(28, 28)
        remove_btn.clicked.connect(lambda: self.removed.emit(self.combatant))
        layout.addWidget(remove_btn)

    def _on_fast_toggle(self, checked: bool):
        self.combatant.is_fast = checked
        self._update_fast_btn()
        self.changed.emit()

    def _update_fast_btn(self):
        if self.combatant.is_fast:
            self._fast_btn.setText("⚡ FAST")
            self._fast_btn.setStyleSheet(
                "background-color: #c4a35a; color: #1a1a2e; font-weight: bold; border-radius: 4px;"
            )
        else:
            self._fast_btn.setText("🐢 SLOW")
            self._fast_btn.setStyleSheet(
                "background-color: #2a2a4a; color: #8a7e6b; border-radius: 4px;"
            )

    def _on_acted(self, state):
        self.combatant.acted = bool(state)
        self._update_style()

    def _update_style(self):
        if self.combatant.acted:
            self.setStyleSheet("""
                CombatantCard {
                    background-color: #12182a;
                    border: 1px solid #2a2a4a;
                    border-radius: 8px;
                    opacity: 0.5;
                }
            """)
            self._name_label.setStyleSheet("color: #5a5548;")
        else:
            self.setStyleSheet("""
                CombatantCard {
                    background-color: #16213e;
                    border: 1px solid #2a2a4a;
                    border-radius: 8px;
                }
            """)
            self._name_label.setStyleSheet("color: #e0d6c8;")

    def _on_hp_changed(self, val):
        self.combatant.hp_current = val

    def _on_notes_changed(self, text):
        self.combatant.notes = text

    def reset_turn(self):
        """Reset the acted state for a new round."""
        self.combatant.acted = False
        self._acted_check.setChecked(False)
        self._update_style()


class InitiativePage(QWidget):
    """SotDL Initiative Tracker — Fast/Slow turn system."""

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._combatants: list[Combatant] = []
        self._cards: list[CombatantCard] = []
        self._round = 0
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("⚔️  Initiative Tracker")
        title.setObjectName("heading")
        title_row.addWidget(title)
        title_row.addStretch()

        self._round_label = QLabel("Round: 0")
        self._round_label.setObjectName("subheading")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self._round_label.setFont(font)
        title_row.addWidget(self._round_label)
        layout.addLayout(title_row)

        subtitle = QLabel("Fast turns act first (one action), then slow turns (two actions). PCs before NPCs.")
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # ── Add Combatant ───────────────────────────────────────
        add_group = QGroupBox("Add Combatant")
        ag = QHBoxLayout(add_group)

        ag.addWidget(QLabel("Name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Combatant name")
        self._name_edit.returnPressed.connect(self._add_combatant)
        ag.addWidget(self._name_edit, stretch=1)

        ag.addWidget(QLabel("HP:"))
        self._hp_spin = QSpinBox()
        self._hp_spin.setRange(0, 999)
        self._hp_spin.setValue(0)
        self._hp_spin.setFixedWidth(70)
        self._hp_spin.setToolTip("0 = no HP tracking")
        ag.addWidget(self._hp_spin)

        self._pc_check = QCheckBox("PC")
        self._pc_check.setChecked(True)
        ag.addWidget(self._pc_check)

        add_btn = QPushButton("✚ Add")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self._add_combatant)
        ag.addWidget(add_btn)

        layout.addWidget(add_group)

        # ── Round Controls ──────────────────────────────────────
        ctrl_row = QHBoxLayout()

        next_round_btn = QPushButton("▶ Next Round")
        next_round_btn.setObjectName("primary")
        next_round_btn.setMinimumHeight(38)
        next_round_btn.clicked.connect(self._next_round)
        ctrl_row.addWidget(next_round_btn)

        reset_btn = QPushButton("⟲ Reset Combat")
        reset_btn.setMinimumHeight(38)
        reset_btn.clicked.connect(self._reset_combat)
        ctrl_row.addWidget(reset_btn)

        all_slow_btn = QPushButton("All Slow")
        all_slow_btn.setMinimumHeight(38)
        all_slow_btn.clicked.connect(self._all_slow)
        ctrl_row.addWidget(all_slow_btn)

        ctrl_row.addStretch()
        layout.addLayout(ctrl_row)

        # ── Turn Order Display ──────────────────────────────────
        self._order_scroll = QScrollArea()
        self._order_scroll.setWidgetResizable(True)
        self._order_scroll.setFrameShape(QFrame.NoFrame)

        self._order_widget = QWidget()
        self._order_layout = QVBoxLayout(self._order_widget)
        self._order_layout.setContentsMargins(0, 0, 0, 0)
        self._order_layout.setSpacing(4)
        self._order_layout.addStretch()

        self._order_scroll.setWidget(self._order_widget)
        layout.addWidget(self._order_scroll, stretch=1)

    # ── Actions ─────────────────────────────────────────────────

    def _add_combatant(self):
        name = self._name_edit.text().strip()
        if not name:
            return
        is_pc = self._pc_check.isChecked()
        hp = self._hp_spin.value()

        combatant = Combatant(name, is_pc, hp)
        self._combatants.append(combatant)
        self._name_edit.clear()
        self._rebuild_order()

    def _remove_combatant(self, combatant: Combatant):
        if combatant in self._combatants:
            self._combatants.remove(combatant)
            self._rebuild_order()

    def _next_round(self):
        self._round += 1
        self._round_label.setText(f"Round: {self._round}")

        # Reset all acted states
        for card in self._cards:
            card.reset_turn()

    def _reset_combat(self):
        reply = QMessageBox.question(
            self, "Reset Combat",
            "Clear all combatants and reset the round counter?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._combatants.clear()
            self._round = 0
            self._round_label.setText("Round: 0")
            self._rebuild_order()

    def _all_slow(self):
        """Set all combatants to slow turn."""
        for c in self._combatants:
            c.is_fast = False
        self._rebuild_order()

    def _rebuild_order(self):
        """Rebuild the turn order display: Fast PCs → Fast NPCs → Slow PCs → Slow NPCs."""
        # Clear existing cards
        self._cards.clear()
        while self._order_layout.count() > 0:
            item = self._order_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Sort: fast before slow, PCs before NPCs within each group
        groups = [
            ("⚡ Fast Turn — PCs", [c for c in self._combatants if c.is_fast and c.is_pc]),
            ("⚡ Fast Turn — NPCs", [c for c in self._combatants if c.is_fast and not c.is_pc]),
            ("🐢 Slow Turn — PCs", [c for c in self._combatants if not c.is_fast and c.is_pc]),
            ("🐢 Slow Turn — NPCs", [c for c in self._combatants if not c.is_fast and not c.is_pc]),
        ]

        for group_label, members in groups:
            if not members:
                continue

            header = QLabel(group_label)
            header.setObjectName("subheading")
            header.setStyleSheet("padding: 8px 0 4px 0;")
            self._order_layout.addWidget(header)

            for combatant in members:
                card = CombatantCard(combatant)
                card.removed.connect(self._remove_combatant)
                card.changed.connect(self._rebuild_order)
                self._cards.append(card)
                self._order_layout.addWidget(card)

        self._order_layout.addStretch()
