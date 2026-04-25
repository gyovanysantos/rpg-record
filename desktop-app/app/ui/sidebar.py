"""
Sidebar — vertical navigation panel on the left side of the main window.

Each button switches the QStackedWidget to show the corresponding page.
Buttons are styled as checked/unchecked via the QSS 'active' property.
The DM role sees all pages; the Player role hides the Recorder page.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt


# (icon_text, page_key, label, dm_only)
NAV_ITEMS = [
    ("🏠", "dashboard",   "Dashboard",   False),
    ("🎙️", "recorder",    "Recorder",    True),
    ("📜", "transcript",  "Transcripts", False),
    ("🧙", "characters",  "Characters",  False),
    ("⚔️", "initiative",  "Initiative",  False),
    ("🎲", "dice",        "Dice Roller", False),
    ("🔊", "narrator",    "Narrator",    True),
    ("⚙️", "settings",    "Settings",    True),
]


class Sidebar(QWidget):
    """Vertical navigation sidebar that emits `page_changed(key)` signals."""

    page_changed = Signal(str)

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(180)

        self._role = role
        self._buttons: dict[str, QPushButton] = {}
        self._build_ui()

    # ── UI Construction ─────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(4)

        # App title in sidebar
        title = QLabel("SotDL")
        title.setObjectName("heading")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(16)

        for icon, key, label, dm_only in NAV_ITEMS:
            if dm_only and self._role != "dm":
                continue

            btn = QPushButton(f"  {icon}  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._on_click(k))
            layout.addWidget(btn)
            self._buttons[key] = btn

        layout.addStretch()

    # ── Public API ──────────────────────────────────────────────

    def select(self, key: str):
        """Programmatically select a page (e.g. on startup)."""
        self._on_click(key)

    # ── Internal ────────────────────────────────────────────────

    def _on_click(self, key: str):
        # Update visual state — only one button looks active at a time
        for k, btn in self._buttons.items():
            btn.setChecked(k == key)
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.page_changed.emit(key)
