"""
Player Card Widget — shows a player's name and a live RMS level meter.

Each card is a compact panel displaying:
  - Channel number + player name
  - Animated horizontal level bar (fills based on RMS 0.0–1.0)
  - Peak indicator that decays slowly for visual feedback
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QLinearGradient


class LevelBar(QWidget):
    """Custom-painted horizontal audio level meter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(18)
        self.setMinimumWidth(120)
        self._level = 0.0      # Current level 0.0–1.0
        self._peak = 0.0       # Peak hold level
        self._peak_decay = 0.02  # How fast peak falls per paint

    def set_level(self, value: float):
        """Update the current level (0.0 to 1.0)."""
        self._level = max(0.0, min(1.0, value))
        if self._level > self._peak:
            self._peak = self._level
        else:
            self._peak = max(self._level, self._peak - self._peak_decay)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background track
        painter.setBrush(QColor("#0d1117"))
        painter.setPen(QColor("#2a2a4a"))
        painter.drawRoundedRect(0, 0, w, h, 4, 4)

        # Level fill with gradient (green → gold → red)
        if self._level > 0.01:
            fill_w = int(w * self._level)
            gradient = QLinearGradient(0, 0, w, 0)
            gradient.setColorAt(0.0, QColor("#2e5e3e"))   # Green (quiet)
            gradient.setColorAt(0.6, QColor("#c4a35a"))   # Gold (moderate)
            gradient.setColorAt(1.0, QColor("#8b0000"))   # Red (loud/clipping)

            painter.setPen(Qt.NoPen)
            painter.setBrush(gradient)
            painter.drawRoundedRect(1, 1, fill_w - 2, h - 2, 3, 3)

        # Peak indicator line
        if self._peak > 0.02:
            peak_x = int(w * self._peak)
            painter.setPen(QColor("#c4a35a"))
            painter.drawLine(peak_x, 2, peak_x, h - 2)

        painter.end()


class PlayerCard(QFrame):
    """
    A card showing player info and their live audio level.

    Layout:
    ┌──────────────────────────────────┐
    │  CH 0 — Dungeon Master   [████] │
    └──────────────────────────────────┘
    """

    def __init__(self, channel: int, player_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._channel = channel
        self._player_name = player_name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Channel + player name
        info = QVBoxLayout()
        info.setSpacing(2)

        ch_label = QLabel(f"CH {channel}")
        ch_label.setObjectName("muted")
        ch_label.setFixedWidth(40)
        info.addWidget(ch_label)

        name_label = QLabel(player_name)
        name_label.setObjectName("subheading")
        name_label.setFixedWidth(140)
        info.addWidget(name_label)

        layout.addLayout(info)

        # Level meter
        self._level_bar = LevelBar()
        layout.addWidget(self._level_bar, stretch=1)

    def set_level(self, value: float):
        """Update the level meter for this player's channel."""
        self._level_bar.set_level(value)

    def reset(self):
        """Reset the meter to zero."""
        self._level_bar.set_level(0.0)
