"""
Transcript Viewer Page — browse and search session transcripts.

Features:
- Session selector dropdown (scans sessions/ for merged transcripts)
- Color-coded speaker lines (each player gets a unique color)
- Full-text search with highlighting
- Summary viewer (loads summary.md if available)
- Export to clipboard
- Per-channel JSON transcript viewer
"""

import re
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QComboBox, QLineEdit, QTextEdit, QScrollArea,
    QFrame, QSplitter, QTabWidget, QApplication, QFileDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor

from app.models.campaign import scan_all_sessions, SessionInfo

# Speaker colors — distinct, readable on dark backgrounds
_SPEAKER_COLORS = [
    "#c4a35a",  # gold
    "#5e9ed6",  # steel blue
    "#7ec88b",  # sage green
    "#d47d7d",  # muted red
    "#b88cd4",  # lavender
    "#d4a76a",  # amber
    "#6bc5c5",  # teal
    "#d4708a",  # rose
    "#8ab86b",  # olive green
    "#c49a5e",  # warm bronze
]


def _color_for_speaker(name: str, mapping: dict[str, str]) -> str:
    """Get a consistent color for a speaker name."""
    if name not in mapping:
        idx = len(mapping) % len(_SPEAKER_COLORS)
        mapping[name] = _SPEAKER_COLORS[idx]
    return mapping[name]


class TranscriptPage(QWidget):
    """Transcript viewer with speaker colors, search, and export."""

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._sessions: list[SessionInfo] = []
        self._current_lines: list[str] = []
        self._speaker_colors: dict[str, str] = {}
        self._build_ui()
        self._refresh_sessions()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        title = QLabel("📜  Transcripts")
        title.setObjectName("heading")
        layout.addWidget(title)

        # ── Controls row ────────────────────────────────────────
        controls = QHBoxLayout()
        controls.setSpacing(12)

        controls.addWidget(QLabel("Session:"))
        self._session_combo = QComboBox()
        self._session_combo.setMinimumWidth(250)
        self._session_combo.currentIndexChanged.connect(self._on_session_changed)
        controls.addWidget(self._session_combo, stretch=1)

        refresh_btn = QPushButton("⟲ Refresh")
        refresh_btn.clicked.connect(self._refresh_sessions)
        controls.addWidget(refresh_btn)

        layout.addLayout(controls)

        # ── Search bar ──────────────────────────────────────────
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("🔍 Search transcript...")
        self._search_edit.textChanged.connect(self._on_search)
        search_row.addWidget(self._search_edit, stretch=1)

        self._match_label = QLabel("")
        self._match_label.setObjectName("muted")
        self._match_label.setFixedWidth(100)
        search_row.addWidget(self._match_label)

        layout.addLayout(search_row)

        # ── Tabs: Transcript | Summary ──────────────────────────
        tabs = QTabWidget()

        # Transcript tab
        transcript_tab = QWidget()
        tl = QVBoxLayout(transcript_tab)
        tl.setContentsMargins(0, 8, 0, 0)

        self._transcript_view = QTextEdit()
        self._transcript_view.setReadOnly(True)
        self._transcript_view.setFont(QFont("Consolas", 12))
        self._transcript_view.setPlaceholderText(
            "Select a session above to view its transcript.\n\n"
            "Transcripts are created after recording → processing → "
            "transcribing → merging a session."
        )
        tl.addWidget(self._transcript_view, stretch=1)

        # Export buttons
        export_row = QHBoxLayout()
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_transcript)
        export_row.addWidget(copy_btn)

        save_btn = QPushButton("💾 Save As...")
        save_btn.clicked.connect(self._save_transcript)
        export_row.addWidget(save_btn)

        self._speaker_legend = QLabel("")
        self._speaker_legend.setObjectName("muted")
        self._speaker_legend.setWordWrap(True)
        export_row.addWidget(self._speaker_legend, stretch=1)

        tl.addLayout(export_row)
        tabs.addTab(transcript_tab, "📜 Transcript")

        # Summary tab
        summary_tab = QWidget()
        sl = QVBoxLayout(summary_tab)
        sl.setContentsMargins(0, 8, 0, 0)

        self._summary_view = QTextEdit()
        self._summary_view.setReadOnly(True)
        self._summary_view.setFont(QFont("Segoe UI", 13))
        self._summary_view.setPlaceholderText(
            "No summary available for this session.\n\n"
            "Summaries are generated after merging transcripts."
        )
        sl.addWidget(self._summary_view, stretch=1)

        copy_sum_btn = QPushButton("📋 Copy Summary")
        copy_sum_btn.clicked.connect(self._copy_summary)
        sl.addWidget(copy_sum_btn)

        tabs.addTab(summary_tab, "📝 Summary")

        layout.addWidget(tabs, stretch=1)

    # ── Session Management ──────────────────────────────────────

    def _refresh_sessions(self):
        """Rescan sessions directory and populate the dropdown."""
        self._sessions = scan_all_sessions()
        self._session_combo.blockSignals(True)
        self._session_combo.clear()

        if not self._sessions:
            self._session_combo.addItem("No sessions found")
            self._session_combo.blockSignals(False)
            return

        for s in self._sessions:
            status_icon = {
                "Summarized": "✅",
                "Merged": "📄",
                "Transcribed": "🔤",
                "Processed": "⚙️",
                "Recorded": "🎙️",
                "Empty": "📁",
            }.get(s.status, "📁")
            self._session_combo.addItem(f"{status_icon} {s.name} — {s.status}", s)

        self._session_combo.blockSignals(False)
        self._session_combo.setCurrentIndex(0)
        self._on_session_changed(0)

    def _on_session_changed(self, index: int):
        """Load the selected session's transcript and summary."""
        if index < 0 or index >= len(self._sessions):
            return

        session = self._sessions[index]
        self._speaker_colors.clear()
        self._current_lines.clear()

        # Load merged transcript
        merged_path = session.path / "transcripts" / "merged.txt"
        if merged_path.exists():
            text = merged_path.read_text(encoding="utf-8")
            self._current_lines = text.splitlines()
            self._render_transcript(self._current_lines)
        else:
            self._transcript_view.clear()
            self._transcript_view.setPlaceholderText(
                f"No merged transcript found for {session.name}.\n"
                "Run the full pipeline: Record → Process → Transcribe → Merge"
            )
            self._current_lines = []

        # Load summary
        summary_path = session.path / "summary.md"
        if summary_path.exists():
            self._summary_view.setMarkdown(summary_path.read_text(encoding="utf-8"))
        else:
            self._summary_view.clear()
            self._summary_view.setPlaceholderText("No summary available for this session.")

        # Update legend
        self._update_legend()

    def _render_transcript(self, lines: list[str], highlight: str = ""):
        """Render transcript lines with speaker colors and optional search highlight."""
        self._transcript_view.clear()
        cursor = self._transcript_view.textCursor()

        # Pattern: [MM:SS] Speaker Name: text
        line_pattern = re.compile(r"^\[(\d{2}:\d{2})\]\s+(.+?):\s+(.*)$")

        for line in lines:
            match = line_pattern.match(line)
            if match:
                timestamp, speaker, text = match.groups()
                color = _color_for_speaker(speaker, self._speaker_colors)

                # Timestamp
                ts_fmt = QTextCharFormat()
                ts_fmt.setForeground(QColor("#8a7e6b"))
                cursor.insertText(f"[{timestamp}] ", ts_fmt)

                # Speaker name
                sp_fmt = QTextCharFormat()
                sp_fmt.setForeground(QColor(color))
                sp_fmt.setFontWeight(QFont.Bold)
                cursor.insertText(f"{speaker}: ", sp_fmt)

                # Text (with optional highlight)
                if highlight:
                    self._insert_highlighted(cursor, text, highlight)
                else:
                    txt_fmt = QTextCharFormat()
                    txt_fmt.setForeground(QColor("#e0d6c8"))
                    cursor.insertText(text, txt_fmt)
            else:
                # Non-matching line — just insert as-is
                default_fmt = QTextCharFormat()
                default_fmt.setForeground(QColor("#e0d6c8"))
                cursor.insertText(line, default_fmt)

            cursor.insertText("\n")

        self._transcript_view.setTextCursor(cursor)
        self._transcript_view.moveCursor(QTextCursor.Start)

    def _insert_highlighted(self, cursor: QTextCursor, text: str, query: str):
        """Insert text with search matches highlighted in gold."""
        normal_fmt = QTextCharFormat()
        normal_fmt.setForeground(QColor("#e0d6c8"))

        highlight_fmt = QTextCharFormat()
        highlight_fmt.setBackground(QColor("#c4a35a"))
        highlight_fmt.setForeground(QColor("#1a1a2e"))
        highlight_fmt.setFontWeight(QFont.Bold)

        parts = re.split(f"({re.escape(query)})", text, flags=re.IGNORECASE)
        for part in parts:
            if part.lower() == query.lower():
                cursor.insertText(part, highlight_fmt)
            else:
                cursor.insertText(part, normal_fmt)

    # ── Search ──────────────────────────────────────────────────

    def _on_search(self, query: str):
        """Filter and highlight matching transcript lines."""
        if not self._current_lines:
            return

        if not query.strip():
            self._render_transcript(self._current_lines)
            self._match_label.setText("")
            return

        # Filter lines containing the query
        matching = [l for l in self._current_lines if query.lower() in l.lower()]
        self._render_transcript(matching, highlight=query)
        self._match_label.setText(f"{len(matching)} / {len(self._current_lines)}")

    # ── Export ──────────────────────────────────────────────────

    def _copy_transcript(self):
        """Copy the full (unfiltered) transcript to clipboard."""
        if self._current_lines:
            QApplication.clipboard().setText("\n".join(self._current_lines))

    def _copy_summary(self):
        """Copy the summary to clipboard."""
        text = self._summary_view.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def _save_transcript(self):
        """Save the transcript to a user-chosen file."""
        if not self._current_lines:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Transcript", "", "Text Files (*.txt);;All Files (*)"
        )
        if path:
            Path(path).write_text("\n".join(self._current_lines), encoding="utf-8")

    # ── Legend ──────────────────────────────────────────────────

    def _update_legend(self):
        """Show speaker color legend."""
        if not self._speaker_colors:
            self._speaker_legend.setText("")
            return
        parts = []
        for speaker, color in self._speaker_colors.items():
            parts.append(f'<span style="color: {color}; font-weight: bold;">● {speaker}</span>')
        self._speaker_legend.setText("  ".join(parts))
