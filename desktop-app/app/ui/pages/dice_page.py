"""
Dice Roller Page — SotDL d20 + boons/banes system.

SotDL Dice Mechanics:
- Base roll: 1d20 + attribute modifier
- Boons: add d6s, keep highest single d6 and add to roll
- Banes: add d6s, keep highest single d6 and SUBTRACT from roll
- Boons and banes cancel each other out
- Example: 2 boons + 1 bane = net 1 boon → roll 1d20 + 1d6

Features:
- Modifier input (attribute mod + situational)
- Boon/Bane selectors (cancel each other)
- Big animated result display
- Roll history log
- Quick-roll buttons for common checks
"""

import random
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QSpinBox, QGridLayout, QScrollArea, QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont


class DiceResultLabel(QLabel):
    """Animated label that pulses when a new result is shown."""

    def __init__(self, parent=None):
        super().__init__("—", parent)
        self._scale = 1.0
        self.setAlignment(Qt.AlignCenter)
        font = QFont("Segoe UI", 64, QFont.Bold)
        self.setFont(font)
        self.setMinimumHeight(120)

    def _get_scale(self):
        return self._scale

    def _set_scale(self, val):
        self._scale = val
        size = int(64 * val)
        font = QFont("Segoe UI", max(size, 20), QFont.Bold)
        self.setFont(font)

    scale = Property(float, _get_scale, _set_scale)

    def flash(self):
        """Play a quick scale-up-then-back animation."""
        anim = QPropertyAnimation(self, b"scale", self)
        anim.setDuration(300)
        anim.setStartValue(1.4)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutBounce)
        anim.start(QPropertyAnimation.DeleteWhenStopped)


class DicePage(QWidget):
    """SotDL Dice Roller with boons/banes, modifiers, and history."""

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._history: list[str] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        title = QLabel("🎲  Dice Roller")
        title.setObjectName("heading")
        layout.addWidget(title)

        subtitle = QLabel("d20 + Boons & Banes — Shadow of the Demon Lord")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        # ── Main content: controls + result ─────────────────────
        content = QHBoxLayout()
        content.setSpacing(24)

        # Left: Controls
        controls = QVBoxLayout()
        controls.setSpacing(12)

        # Modifier
        mod_group = QGroupBox("Modifier")
        mg = QHBoxLayout(mod_group)
        mg.addWidget(QLabel("Total Modifier:"))
        self._mod_spin = QSpinBox()
        self._mod_spin.setRange(-20, 30)
        self._mod_spin.setValue(0)
        self._mod_spin.setFixedWidth(80)
        mg.addWidget(self._mod_spin)
        mg.addStretch()
        controls.addWidget(mod_group)

        # Boons & Banes
        bb_group = QGroupBox("Boons & Banes")
        bg = QGridLayout(bb_group)

        bg.addWidget(QLabel("Boons:"), 0, 0)
        self._boons_spin = QSpinBox()
        self._boons_spin.setRange(0, 10)
        self._boons_spin.setFixedWidth(70)
        self._boons_spin.valueChanged.connect(self._update_net)
        bg.addWidget(self._boons_spin, 0, 1)

        bg.addWidget(QLabel("Banes:"), 0, 2)
        self._banes_spin = QSpinBox()
        self._banes_spin.setRange(0, 10)
        self._banes_spin.setFixedWidth(70)
        self._banes_spin.valueChanged.connect(self._update_net)
        bg.addWidget(self._banes_spin, 0, 3)

        self._net_label = QLabel("Net: 0 (flat roll)")
        self._net_label.setObjectName("muted")
        bg.addWidget(self._net_label, 1, 0, 1, 4)

        controls.addWidget(bb_group)

        # Roll Button
        roll_btn = QPushButton("🎲  ROLL d20")
        roll_btn.setObjectName("primary")
        roll_btn.setMinimumHeight(50)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        roll_btn.setFont(font)
        roll_btn.clicked.connect(self._roll)
        controls.addWidget(roll_btn)

        # Quick-roll buttons
        quick_group = QGroupBox("Quick Rolls")
        qg = QGridLayout(quick_group)
        quick_rolls = [
            ("Attack", 0), ("Str Check", 0), ("Agi Check", 0),
            ("Int Check", 0), ("Will Check", 0), ("Challenge", 0),
            ("d6", None), ("2d6", None), ("3d6", None),
        ]
        for i, (label, _mod) in enumerate(quick_rolls):
            btn = QPushButton(label)
            btn.setFixedHeight(32)
            if label in ("d6", "2d6", "3d6"):
                btn.clicked.connect(lambda checked, l=label: self._quick_dice(l))
            else:
                btn.clicked.connect(lambda checked, l=label: self._quick_d20(l))
            qg.addWidget(btn, i // 3, i % 3)
        controls.addWidget(quick_group)
        controls.addStretch()

        content.addLayout(controls, stretch=0)

        # Right: Result + breakdown + history
        result_panel = QVBoxLayout()
        result_panel.setSpacing(12)

        # Result card
        result_card = QFrame()
        result_card.setObjectName("card")
        result_card.setStyleSheet("""
            QFrame#card {
                border: 2px solid #c4a35a;
                border-radius: 16px;
                padding: 16px;
            }
        """)
        rc_layout = QVBoxLayout(result_card)

        self._result_label = DiceResultLabel()
        self._result_label.setStyleSheet("color: #c4a35a;")
        rc_layout.addWidget(self._result_label)

        self._breakdown_label = QLabel("Roll to see the breakdown")
        self._breakdown_label.setObjectName("muted")
        self._breakdown_label.setAlignment(Qt.AlignCenter)
        self._breakdown_label.setWordWrap(True)
        rc_layout.addWidget(self._breakdown_label)

        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setWordWrap(True)
        font2 = QFont()
        font2.setPointSize(12)
        self._status_label.setFont(font2)
        rc_layout.addWidget(self._status_label)

        result_panel.addWidget(result_card)

        # History
        history_group = QGroupBox("Roll History")
        hl = QVBoxLayout(history_group)

        self._history_scroll = QScrollArea()
        self._history_scroll.setWidgetResizable(True)
        self._history_scroll.setFrameShape(QFrame.NoFrame)

        self._history_widget = QWidget()
        self._history_layout = QVBoxLayout(self._history_widget)
        self._history_layout.setContentsMargins(4, 4, 4, 4)
        self._history_layout.setSpacing(4)
        self._history_layout.addStretch()

        self._history_scroll.setWidget(self._history_widget)
        hl.addWidget(self._history_scroll)

        clear_btn = QPushButton("Clear History")
        clear_btn.setFixedHeight(28)
        clear_btn.clicked.connect(self._clear_history)
        hl.addWidget(clear_btn)

        result_panel.addWidget(history_group, stretch=1)

        content.addLayout(result_panel, stretch=1)
        layout.addLayout(content, stretch=1)

    # ── Logic ───────────────────────────────────────────────────

    def _update_net(self):
        boons = self._boons_spin.value()
        banes = self._banes_spin.value()
        net = boons - banes
        if net > 0:
            self._net_label.setText(f"Net: {net} boon(s) → roll {net}d6, keep highest")
        elif net < 0:
            self._net_label.setText(f"Net: {abs(net)} bane(s) → roll {abs(net)}d6, subtract highest")
        else:
            self._net_label.setText("Net: 0 (flat roll)")

    def _roll(self):
        """Perform the full SotDL roll: d20 + modifier ± boon/bane."""
        mod = self._mod_spin.value()
        boons = self._boons_spin.value()
        banes = self._banes_spin.value()

        d20 = random.randint(1, 20)
        net = boons - banes

        bonus_dice = []
        boon_value = 0
        breakdown_parts = [f"d20={d20}"]

        if net != 0:
            count = abs(net)
            bonus_dice = [random.randint(1, 6) for _ in range(count)]
            boon_value = max(bonus_dice)
            dice_str = ", ".join(str(d) for d in bonus_dice)

            if net > 0:
                breakdown_parts.append(f"boons [{dice_str}] → +{boon_value}")
                total = d20 + mod + boon_value
            else:
                breakdown_parts.append(f"banes [{dice_str}] → −{boon_value}")
                total = d20 + mod - boon_value
        else:
            total = d20 + mod

        if mod != 0:
            sign = "+" if mod >= 0 else ""
            breakdown_parts.append(f"mod {sign}{mod}")

        breakdown = "  |  ".join(breakdown_parts)
        self._result_label.setText(str(total))
        self._result_label.flash()
        self._breakdown_label.setText(breakdown)

        # Status message (crit / success thresholds)
        if d20 == 20:
            self._status_label.setText("⚡ NATURAL 20!")
            self._status_label.setStyleSheet("color: #c4a35a; font-weight: bold;")
        elif d20 == 1:
            self._status_label.setText("💀 NATURAL 1...")
            self._status_label.setStyleSheet("color: #8b0000; font-weight: bold;")
        elif total >= 20:
            self._status_label.setText("✦ Great success!")
            self._status_label.setStyleSheet("color: #2e5e3e;")
        elif total >= 10:
            self._status_label.setText("✓ Success (vs 10)")
            self._status_label.setStyleSheet("color: #e0d6c8;")
        else:
            self._status_label.setText("✗ Failure (vs 10)")
            self._status_label.setStyleSheet("color: #8b0000;")

        # Add to history
        now = datetime.now().strftime("%H:%M:%S")
        boon_str = ""
        if net > 0:
            boon_str = f" +{net}B"
        elif net < 0:
            boon_str = f" +{abs(net)}b"
        entry = f"[{now}]  d20{boon_str} {'+' if mod >= 0 else ''}{mod} = {total}  (d20={d20})"
        self._add_history(entry, d20)

    def _quick_d20(self, label: str):
        """Quick roll a d20 with current boons/banes settings."""
        self._roll()
        # Prepend the label to the last history entry
        if self._history:
            last = self._history[-1]
            self._history[-1] = f"{label}: {last.split(']')[1].strip()}" if ']' in last else last

    def _quick_dice(self, label: str):
        """Roll simple dice (d6, 2d6, 3d6) — no boons/banes."""
        count = int(label[0]) if label[0].isdigit() else 1
        dice = [random.randint(1, 6) for _ in range(count)]
        total = sum(dice)
        dice_str = " + ".join(str(d) for d in dice)

        self._result_label.setText(str(total))
        self._result_label.flash()
        self._breakdown_label.setText(f"{label}: [{dice_str}] = {total}")
        self._status_label.setText("")

        now = datetime.now().strftime("%H:%M:%S")
        entry = f"[{now}]  {label} = {total}  [{dice_str}]"
        self._add_history(entry)

    def _add_history(self, text: str, d20_value: int | None = None):
        self._history.append(text)

        entry_label = QLabel(text)
        entry_label.setWordWrap(True)
        entry_label.setStyleSheet("padding: 4px 8px; border-bottom: 1px solid #2a2a4a;")

        if d20_value == 20:
            entry_label.setStyleSheet(entry_label.styleSheet() + "color: #c4a35a; font-weight: bold;")
        elif d20_value == 1:
            entry_label.setStyleSheet(entry_label.styleSheet() + "color: #8b0000;")

        # Insert before the stretch
        count = self._history_layout.count()
        self._history_layout.insertWidget(count - 1, entry_label)

        # Auto-scroll to bottom
        self._history_scroll.verticalScrollBar().setValue(
            self._history_scroll.verticalScrollBar().maximum()
        )

    def _clear_history(self):
        self._history.clear()
        while self._history_layout.count() > 1:
            item = self._history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
