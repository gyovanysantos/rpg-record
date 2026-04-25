"""
Dashboard Page — Campaign overview and session history.

Shows:
- Campaign header with quick stats
- Session history as cards (newest first)
- Each session card shows date, status, transcript preview
- Create campaign dialog
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QScrollArea, QFrame, QGridLayout,
    QDialog, QLineEdit, QTextEdit, QDialogButtonBox,
)
from PySide6.QtCore import Qt, QTimer

from app.models.campaign import (
    scan_all_sessions, SessionInfo,
    load_campaigns, create_campaign,
)


class DashboardPage(QWidget):
    """Campaign dashboard — session history and campaign overview."""

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._build_ui()
        # Defer data loading so the window can render first
        QTimer.singleShot(100, self._refresh)

    # ── UI Construction ─────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ── Title Row ───────────────────────────────────────────
        title_row = QHBoxLayout()
        title = QLabel("🏰  Campaign Dashboard")
        title.setObjectName("heading")
        title_row.addWidget(title)
        title_row.addStretch()

        refresh_btn = QPushButton("⟳  Refresh")
        refresh_btn.setObjectName("primary")
        refresh_btn.setFixedWidth(120)
        refresh_btn.clicked.connect(self._refresh)
        title_row.addWidget(refresh_btn)

        layout.addLayout(title_row)

        # ── Stats Row ──────────────────────────────────────────
        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(16)

        self._stat_total = self._make_stat_card("Total Sessions", "0")
        self._stat_latest = self._make_stat_card("Latest Session", "—")
        self._stat_transcribed = self._make_stat_card("Transcribed", "0")
        self._stat_summarized = self._make_stat_card("Summarized", "0")

        self._stats_row.addWidget(self._stat_total)
        self._stats_row.addWidget(self._stat_latest)
        self._stats_row.addWidget(self._stat_transcribed)
        self._stats_row.addWidget(self._stat_summarized)
        self._stats_row.addStretch()

        layout.addLayout(self._stats_row)

        # ── Session History ────────────────────────────────────
        history_label = QLabel("📜  Session History")
        history_label.setObjectName("subheading")
        layout.addWidget(history_label)

        # Scrollable area for session cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._sessions_container = QWidget()
        self._sessions_layout = QVBoxLayout(self._sessions_container)
        self._sessions_layout.setContentsMargins(0, 0, 8, 0)
        self._sessions_layout.setSpacing(8)
        self._sessions_layout.addStretch()

        scroll.setWidget(self._sessions_container)
        layout.addWidget(scroll, stretch=1)

    # ── Stat Cards ──────────────────────────────────────────────

    def _make_stat_card(self, label: str, value: str) -> QFrame:
        """Create a small stat display card."""
        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(160, 80)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(12, 8, 12, 8)
        vbox.setSpacing(4)

        val_label = QLabel(value)
        val_label.setObjectName("heading")
        val_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(val_label)

        name_label = QLabel(label)
        name_label.setObjectName("muted")
        name_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(name_label)

        # Store reference to value label for updates
        card._value_label = val_label
        return card

    def _update_stat(self, card: QFrame, value: str):
        card._value_label.setText(value)

    # ── Session Cards ───────────────────────────────────────────

    def _make_session_card(self, session: SessionInfo) -> QFrame:
        """Create a card widget for a single session."""
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(100)

        hbox = QHBoxLayout(card)
        hbox.setContentsMargins(16, 12, 16, 12)
        hbox.setSpacing(16)

        # ── Left: Status + Date ─────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(4)

        date_str = session.date.strftime("%b %d, %Y") if session.date else session.name
        date_label = QLabel(f"📅  {date_str}")
        date_label.setObjectName("subheading")
        left.addWidget(date_label)

        folder_label = QLabel(session.name)
        folder_label.setObjectName("muted")
        left.addWidget(folder_label)

        status_label = QLabel(f"{session.status_icon}  {session.status}")
        left.addWidget(status_label)

        left.addStretch()
        hbox.addLayout(left)

        # ── Center: Preview ─────────────────────────────────
        center = QVBoxLayout()
        center.setSpacing(4)

        if session.transcript_preview:
            preview = QLabel(session.transcript_preview)
            preview.setObjectName("muted")
            preview.setWordWrap(True)
            preview.setMaximumHeight(60)
            center.addWidget(preview)
        elif session.has_raw:
            info = QLabel(f"🎙️  {session.raw_file_count} channel(s) recorded")
            info.setObjectName("muted")
            center.addWidget(info)
        else:
            empty = QLabel("No data yet")
            empty.setObjectName("muted")
            center.addWidget(empty)

        center.addStretch()
        hbox.addLayout(center, stretch=1)

        # ── Right: Actions ──────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(4)

        if session.has_summary:
            summary_btn = QPushButton("📄 Summary")
            summary_btn.setFixedWidth(100)
            summary_btn.clicked.connect(
                lambda checked, s=session: self._show_summary(s)
            )
            right.addWidget(summary_btn)

        if session.has_merged:
            transcript_btn = QPushButton("📋 Transcript")
            transcript_btn.setFixedWidth(100)
            transcript_btn.clicked.connect(
                lambda checked, s=session: self._show_transcript(s)
            )
            right.addWidget(transcript_btn)

        open_btn = QPushButton("📂 Open")
        open_btn.setFixedWidth(100)
        open_btn.clicked.connect(
            lambda checked, s=session: self._open_folder(s)
        )
        right.addWidget(open_btn)

        right.addStretch()
        hbox.addLayout(right)

        return card

    # ── Data Loading ────────────────────────────────────────────

    def _refresh(self):
        """Scan sessions directory and rebuild the dashboard."""
        sessions = scan_all_sessions()

        # Update stats
        self._update_stat(self._stat_total, str(len(sessions)))
        self._update_stat(
            self._stat_latest,
            sessions[0].date.strftime("%b %d") if sessions and sessions[0].date else "—",
        )
        self._update_stat(
            self._stat_transcribed,
            str(sum(1 for s in sessions if s.has_transcript)),
        )
        self._update_stat(
            self._stat_summarized,
            str(sum(1 for s in sessions if s.has_summary)),
        )

        # Clear existing session cards
        while self._sessions_layout.count() > 0:
            item = self._sessions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add session cards (newest first)
        if sessions:
            for session in sessions:
                card = self._make_session_card(session)
                self._sessions_layout.addWidget(card)
        else:
            empty = QLabel("No sessions yet. Go to Recorder to start your first session!")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignCenter)
            self._sessions_layout.addWidget(empty)

        self._sessions_layout.addStretch()

    # ── Actions ─────────────────────────────────────────────────

    def _show_summary(self, session: SessionInfo):
        """Show summary in a dialog."""
        summary_file = session.path / "summary.md"
        if not summary_file.exists():
            return

        text = summary_file.read_text(encoding="utf-8")
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Summary — {session.name}")
        dlg.setMinimumSize(600, 400)

        layout = QVBoxLayout(dlg)
        content = QTextEdit()
        content.setReadOnly(True)
        content.setPlainText(text)
        layout.addWidget(content)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        dlg.exec()

    def _show_transcript(self, session: SessionInfo):
        """Show merged transcript in a dialog."""
        merged_file = session.path / "transcripts" / "merged.txt"
        if not merged_file.exists():
            return

        text = merged_file.read_text(encoding="utf-8")
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Transcript — {session.name}")
        dlg.setMinimumSize(600, 400)

        layout = QVBoxLayout(dlg)
        content = QTextEdit()
        content.setReadOnly(True)
        content.setPlainText(text)
        layout.addWidget(content)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        dlg.exec()

    def _open_folder(self, session: SessionInfo):
        """Open the session folder in the system file explorer."""
        import subprocess
        import sys

        path = str(session.path)
        if sys.platform == "win32":
            subprocess.Popen(["explorer", path])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
