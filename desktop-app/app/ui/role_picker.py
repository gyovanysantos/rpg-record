"""
Role Picker Dialog — first screen the user sees.

Presents two large buttons: Dungeon Master or Player.
The chosen role determines which features are available in the main window.
DM gets recording + all tools; Player gets viewing + RPG tools only.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)
from PySide6.QtCore import Qt


class RolePickerDialog(QDialog):
    """Modal dialog that asks the user to pick DM or Player role."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Shadow of the Demon Lord — Choose Your Role")
        self.setFixedSize(600, 400)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )

        self._role = None  # Will be "dm" or "player"
        self._build_ui()

    # ── Public API ──────────────────────────────────────────────

    def chosen_role(self) -> str | None:
        """Return 'dm' or 'player', or None if dialog was cancelled."""
        return self._role

    # ── UI Construction ─────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(40, 30, 40, 30)

        # Title
        title = QLabel("⚔️  Shadow of the Demon Lord  ⚔️")
        title.setObjectName("heading")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Choose your role for this session")
        subtitle.setObjectName("subheading")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addStretch()

        # Role buttons (side by side)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(32)

        self._dm_btn = self._make_role_button(
            "🎭\nDungeon Master",
            "Record sessions, manage campaigns,\nfull access to all tools",
        )
        self._dm_btn.clicked.connect(lambda: self._pick("dm"))

        self._player_btn = self._make_role_button(
            "⚔️\nPlayer",
            "View transcripts, character sheets,\ndice roller & initiative tracker",
        )
        self._player_btn.clicked.connect(lambda: self._pick("player"))

        btn_row.addWidget(self._dm_btn)
        btn_row.addWidget(self._player_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

    def _make_role_button(self, label: str, tooltip: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("roleButton")
        btn.setToolTip(tooltip)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        btn.setCursor(Qt.PointingHandCursor)
        return btn

    # ── Slots ───────────────────────────────────────────────────

    def _pick(self, role: str):
        self._role = role
        self.accept()
