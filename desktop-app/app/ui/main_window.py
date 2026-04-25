"""
MainWindow — the primary application window.

Layout:
┌──────────┬─────────────────────────────────┐
│          │                                 │
│ Sidebar  │   Page Stack (QStackedWidget)   │
│  (nav)   │                                 │
│          │                                 │
└──────────┴─────────────────────────────────┘

The sidebar emits `page_changed(key)` signals that switch the
visible page in the stacked widget. The available pages depend
on the user's chosen role (DM sees everything, Player sees a subset).
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QStatusBar,
)
from PySide6.QtCore import Qt

from app.ui.sidebar import Sidebar
from app.ui.pages.narrator_page import NarratorPage
from app.ui.pages.transcript_page import TranscriptPage
from app.ui.pages.dice_page import DicePage
from app.ui.pages.initiative_page import InitiativePage
from app.ui.pages.characters_page import CharactersPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.recorder_page import RecorderPage
from app.ui.pages.settings_page import SettingsPage


class MainWindow(QMainWindow):
    """Central window — sidebar + page stack, role-aware."""

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._role = role
        self.setWindowTitle(f"Shadow of the Demon Lord — {role.upper()}")
        self.setMinimumSize(1100, 700)

        self._pages: dict[str, QWidget] = {}
        self._build_ui()

        # Start on dashboard
        self._sidebar.select("dashboard")

    # ── UI Construction ─────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar(self._role)
        self._sidebar.page_changed.connect(self._switch_page)
        root.addWidget(self._sidebar)

        # Page stack
        self._stack = QStackedWidget()
        self._stack.setObjectName("pageContainer")
        root.addWidget(self._stack, stretch=1)

        # Register pages
        self._add_page("dashboard",  DashboardPage(self._role))
        self._add_page("transcript", TranscriptPage(self._role))
        self._add_page("characters", CharactersPage(self._role))
        self._add_page("initiative", InitiativePage(self._role))
        self._add_page("dice",       DicePage(self._role))

        if self._role == "dm":
            self._add_page("recorder", RecorderPage(self._role))
            self._add_page("narrator", NarratorPage(self._role))
            self._add_page("settings", SettingsPage(self._role))

        # Status bar
        status = QStatusBar()
        role_display = "Dungeon Master" if self._role == "dm" else "Player"
        status.showMessage(f"Role: {role_display}  |  Shadow of the Demon Lord")
        self.setStatusBar(status)

    def _add_page(self, key: str, page: QWidget):
        self._pages[key] = page
        self._stack.addWidget(page)

    # ── Slots ───────────────────────────────────────────────────

    def _switch_page(self, key: str):
        page = self._pages.get(key)
        if page:
            self._stack.setCurrentWidget(page)
