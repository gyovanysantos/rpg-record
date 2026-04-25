"""
Narrator Page — Cinematic TTS narration of session recaps.

Features:
- Session selector with summary preview
- Voice picker (30 Gemini TTS voices, curated dark-fantasy subset)
- Narration style selector (Dark & Ominous, Epic & Heroic, etc.)
- Two-step pipeline: summary → dramatic script → TTS audio
- Built-in audio player (play/pause/stop, seek slider, time display)
- Script editor (view/edit before generating audio)
- Export: save WAV, copy script
"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QComboBox, QTextEdit, QProgressBar,
    QSlider, QApplication, QFileDialog, QSplitter,
)
from PySide6.QtCore import Qt, QThread, QUrl, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtGui import QFont

from app.models.campaign import scan_all_sessions, SessionInfo
from app.core.narrator_worker import (
    NarratorWorker, VOICES, NARRATION_STYLES,
    DEFAULT_VOICE, DEFAULT_STYLE,
)
from app.core.settings_manager import get_model


def _load_api_key() -> str:
    """Load GEMINI_API_KEY from .env or environment."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    # Try loading from .env file at repo root
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


class NarratorPage(QWidget):
    """Cinematic narration page with TTS generation and audio playback."""

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._sessions: list[SessionInfo] = []
        self._worker: NarratorWorker | None = None
        self._thread: QThread | None = None
        self._current_audio_path: str = ""
        self._build_ui()
        self._setup_player()
        self._refresh_sessions()

    # ── UI Construction ─────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        title = QLabel("🔊  Cinematic Narrator")
        title.setObjectName("heading")
        layout.addWidget(title)

        subtitle = QLabel(
            "Transform session summaries into dramatic narrations "
            "using Gemini TTS — your personal dark fantasy storyteller."
        )
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # ── Controls Row ────────────────────────────────────────
        controls_group = QGroupBox("Session & Voice")
        controls_group.setObjectName("card")
        cl = QVBoxLayout(controls_group)

        # Row 1: Session selector
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Session:"))
        self._session_combo = QComboBox()
        self._session_combo.setMinimumWidth(250)
        self._session_combo.currentIndexChanged.connect(self._on_session_changed)
        row1.addWidget(self._session_combo, stretch=1)

        refresh_btn = QPushButton("⟲")
        refresh_btn.setFixedWidth(36)
        refresh_btn.setToolTip("Refresh sessions")
        refresh_btn.clicked.connect(self._refresh_sessions)
        row1.addWidget(refresh_btn)
        cl.addLayout(row1)

        # Row 2: Voice + Style
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Voice:"))
        self._voice_combo = QComboBox()
        for name, desc in VOICES.items():
            self._voice_combo.addItem(f"{name} — {desc}", name)
        # Default to Charon
        idx = list(VOICES.keys()).index(DEFAULT_VOICE)
        self._voice_combo.setCurrentIndex(idx)
        row2.addWidget(self._voice_combo, stretch=1)

        row2.addWidget(QLabel("Style:"))
        self._style_combo = QComboBox()
        for name in NARRATION_STYLES:
            self._style_combo.addItem(name)
        row2.addWidget(self._style_combo, stretch=1)
        cl.addLayout(row2)

        # Row 3: Generate button + progress
        row3 = QHBoxLayout()
        self._generate_btn = QPushButton("⚔️  Generate Narration")
        self._generate_btn.setObjectName("primary")
        self._generate_btn.setFixedHeight(40)
        self._generate_btn.clicked.connect(self._on_generate)
        row3.addWidget(self._generate_btn)

        self._cancel_btn = QPushButton("✕ Cancel")
        self._cancel_btn.setObjectName("danger")
        self._cancel_btn.setFixedHeight(40)
        self._cancel_btn.setFixedWidth(100)
        self._cancel_btn.setVisible(False)
        self._cancel_btn.clicked.connect(self._on_cancel)
        row3.addWidget(self._cancel_btn)
        cl.addLayout(row3)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # indeterminate
        self._progress_bar.setVisible(False)
        self._progress_bar.setFixedHeight(6)
        cl.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        self._status_label.setObjectName("muted")
        cl.addWidget(self._status_label)

        layout.addWidget(controls_group)

        # ── Splitter: Script + Audio Player ─────────────────────
        splitter = QSplitter(Qt.Vertical)

        # Script panel
        script_group = QGroupBox("📜 Narration Script")
        script_group.setObjectName("card")
        sl = QVBoxLayout(script_group)

        self._script_view = QTextEdit()
        self._script_view.setFont(QFont("Segoe UI", 12))
        self._script_view.setPlaceholderText(
            "The generated narration script will appear here.\n\n"
            "Select a session with a summary, choose a voice and style, "
            "then click 'Generate Narration'.\n\n"
            "You can edit the script before generating audio by clicking "
            "'🔊 Regenerate Audio Only' after editing."
        )
        sl.addWidget(self._script_view, stretch=1)

        script_buttons = QHBoxLayout()
        self._copy_script_btn = QPushButton("📋 Copy Script")
        self._copy_script_btn.clicked.connect(self._copy_script)
        script_buttons.addWidget(self._copy_script_btn)

        self._regen_audio_btn = QPushButton("🔊 Regenerate Audio Only")
        self._regen_audio_btn.setToolTip(
            "Use the current script text (with your edits) to regenerate audio"
        )
        self._regen_audio_btn.clicked.connect(self._on_regen_audio)
        self._regen_audio_btn.setEnabled(False)
        script_buttons.addWidget(self._regen_audio_btn)

        script_buttons.addStretch()
        sl.addLayout(script_buttons)
        splitter.addWidget(script_group)

        # Audio player panel
        player_group = QGroupBox("🎧 Audio Player")
        player_group.setObjectName("card")
        pl = QVBoxLayout(player_group)

        # Time + seek bar
        time_row = QHBoxLayout()
        self._time_label = QLabel("0:00")
        self._time_label.setFixedWidth(50)
        time_row.addWidget(self._time_label)

        self._seek_slider = QSlider(Qt.Horizontal)
        self._seek_slider.setRange(0, 0)
        self._seek_slider.sliderMoved.connect(self._on_seek)
        time_row.addWidget(self._seek_slider, stretch=1)

        self._duration_label = QLabel("0:00")
        self._duration_label.setFixedWidth(50)
        time_row.addWidget(self._duration_label)
        pl.addLayout(time_row)

        # Playback controls
        btn_row = QHBoxLayout()
        self._play_btn = QPushButton("▶  Play")
        self._play_btn.setObjectName("primary")
        self._play_btn.setFixedHeight(36)
        self._play_btn.clicked.connect(self._on_play_pause)
        self._play_btn.setEnabled(False)
        btn_row.addWidget(self._play_btn)

        self._stop_btn = QPushButton("⏹  Stop")
        self._stop_btn.setFixedHeight(36)
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)
        btn_row.addWidget(self._stop_btn)

        btn_row.addStretch()

        self._save_audio_btn = QPushButton("💾 Save Audio As...")
        self._save_audio_btn.clicked.connect(self._save_audio)
        self._save_audio_btn.setEnabled(False)
        btn_row.addWidget(self._save_audio_btn)

        pl.addLayout(btn_row)

        self._player_status = QLabel("No audio loaded")
        self._player_status.setObjectName("muted")
        pl.addWidget(self._player_status)

        splitter.addWidget(player_group)

        # Set initial sizes (script bigger than player)
        splitter.setSizes([400, 200])
        layout.addWidget(splitter, stretch=1)

        # ── API Key Warning ─────────────────────────────────────
        self._api_warning = QLabel(
            "⚠️  GEMINI_API_KEY not found in .env file. "
            "Add it to use the narrator feature. "
            "Get a key at: https://aistudio.google.com/apikey"
        )
        self._api_warning.setObjectName("danger")
        self._api_warning.setWordWrap(True)
        self._api_warning.setVisible(not bool(_load_api_key()))
        layout.addWidget(self._api_warning)

    # ── Audio Player Setup ──────────────────────────────────────

    def _setup_player(self):
        """Initialize QMediaPlayer and QAudioOutput."""
        self._audio_output = QAudioOutput()
        self._audio_output.setVolume(1.0)

        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state)

    # ── Session Management ──────────────────────────────────────

    def _refresh_sessions(self):
        """Scan sessions and populate the dropdown (only those with summaries)."""
        self._sessions = scan_all_sessions()
        self._session_combo.blockSignals(True)
        self._session_combo.clear()

        # Only show sessions that have summaries
        sessions_with_summaries = [
            s for s in self._sessions
            if (s.path / "summary.md").exists()
        ]

        if not sessions_with_summaries:
            self._session_combo.addItem("No sessions with summaries found")
            self._sessions = []
            self._session_combo.blockSignals(False)
            return

        self._sessions = sessions_with_summaries
        for s in self._sessions:
            self._session_combo.addItem(f"✅ {s.name}", s)

        self._session_combo.blockSignals(False)
        self._session_combo.setCurrentIndex(0)
        self._on_session_changed(0)

    def _on_session_changed(self, index: int):
        """Load summary preview and check for existing narration."""
        if index < 0 or index >= len(self._sessions):
            return

        session = self._sessions[index]
        summary_path = session.path / "summary.md"
        if summary_path.exists():
            self._status_label.setText(f"Summary loaded: {summary_path.name}")
        else:
            self._status_label.setText("No summary available for this session")

        # Check for existing narration audio
        narration_path = session.path / "narration.wav"
        if narration_path.exists():
            self._load_audio(str(narration_path))
            self._player_status.setText(f"🎧 Previous narration found: {narration_path.name}")
            # Also load existing script if available
            script_path = session.path / "narration_script.txt"
            if script_path.exists():
                self._script_view.setPlainText(
                    script_path.read_text(encoding="utf-8")
                )
                self._regen_audio_btn.setEnabled(True)

    # ── Generation ──────────────────────────────────────────────

    def _on_generate(self):
        """Start the full two-step narration pipeline."""
        api_key = _load_api_key()
        if not api_key:
            self._api_warning.setVisible(True)
            self._status_label.setText("❌ GEMINI_API_KEY not set")
            return

        if not self._sessions:
            self._status_label.setText("❌ No session selected")
            return

        index = self._session_combo.currentIndex()
        if index < 0 or index >= len(self._sessions):
            return

        session = self._sessions[index]
        summary_path = session.path / "summary.md"
        if not summary_path.exists():
            self._status_label.setText("❌ No summary.md found")
            return

        summary_text = summary_path.read_text(encoding="utf-8")
        voice = self._voice_combo.currentData()
        style = self._style_combo.currentText()

        self._start_worker(api_key, summary_text, session.path, voice, style)

    def _on_regen_audio(self):
        """Regenerate audio only using the current (possibly edited) script."""
        api_key = _load_api_key()
        if not api_key:
            self._api_warning.setVisible(True)
            return

        script = self._script_view.toPlainText().strip()
        if not script:
            self._status_label.setText("❌ No script to convert")
            return

        if not self._sessions:
            return

        index = self._session_combo.currentIndex()
        if index < 0 or index >= len(self._sessions):
            return

        session = self._sessions[index]
        voice = self._voice_combo.currentData()
        style = self._style_combo.currentText()

        # Use a special mode — skip script generation, go straight to TTS
        self._start_audio_only_worker(api_key, script, session.path, voice, style)

    def _start_worker(self, api_key: str, summary: str, output_dir: Path,
                      voice: str, style: str):
        """Launch the full narration worker on a background thread."""
        self._set_generating(True)

        self._thread = QThread()
        self._worker = NarratorWorker(
            api_key=api_key,
            summary_text=summary,
            output_dir=output_dir,
            voice=voice,
            style=style,
            script_model=get_model("gemini"),
        )
        self._worker.moveToThread(self._thread)

        # Connect signals
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.script_ready.connect(self._on_script_ready)
        self._worker.audio_ready.connect(self._on_audio_ready)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_worker_finished)

        self._thread.start()

    def _start_audio_only_worker(self, api_key: str, script: str,
                                 output_dir: Path, voice: str, style: str):
        """Launch a worker that skips script generation, goes straight to TTS."""
        self._set_generating(True)

        self._thread = QThread()
        self._worker = NarratorWorker(
            api_key=api_key,
            summary_text="",  # won't be used
            output_dir=output_dir,
            voice=voice,
            style=style,
            script_model=get_model("gemini"),
        )
        # Monkey-patch: replace run() to skip script generation
        original_worker = self._worker

        def audio_only_run():
            try:
                from google import genai as _genai
                client = _genai.Client(api_key=api_key)
                original_worker.progress.emit("🔊 Generating audio from script...")
                audio_path = original_worker._generate_audio(client, script)
                original_worker.audio_ready.emit(str(audio_path))
                original_worker.progress.emit("✅  Audio regeneration complete!")
            except Exception as e:
                original_worker.error.emit(str(e))
            finally:
                original_worker.finished.emit()

        self._worker.run = audio_only_run
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)

        self._worker.progress.connect(self._on_progress)
        self._worker.audio_ready.connect(self._on_audio_ready)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_worker_finished)

        self._thread.start()

    def _on_cancel(self):
        """Cancel the current generation."""
        if self._worker:
            self._worker.cancel()
        self._status_label.setText("⚠️ Cancelling...")

    def _set_generating(self, active: bool):
        """Toggle UI state for generation in progress."""
        self._generate_btn.setEnabled(not active)
        self._cancel_btn.setVisible(active)
        self._progress_bar.setVisible(active)
        self._regen_audio_btn.setEnabled(not active)

    # ── Worker Signal Handlers ──────────────────────────────────

    def _on_progress(self, message: str):
        self._status_label.setText(message)

    def _on_script_ready(self, script: str):
        self._script_view.setPlainText(script)
        self._regen_audio_btn.setEnabled(True)

        # Save script to session directory
        index = self._session_combo.currentIndex()
        if 0 <= index < len(self._sessions):
            session = self._sessions[index]
            script_path = session.path / "narration_script.txt"
            script_path.write_text(script, encoding="utf-8")

    def _on_audio_ready(self, audio_path: str):
        self._load_audio(audio_path)
        self._player_status.setText(f"🎧 Audio ready: {Path(audio_path).name}")

    def _on_error(self, message: str):
        self._status_label.setText(f"❌ Error: {message}")

    def _on_worker_finished(self):
        self._set_generating(False)
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None

    # ── Audio Player ────────────────────────────────────────────

    def _load_audio(self, path: str):
        """Load a WAV file into the media player."""
        self._current_audio_path = path
        self._player.setSource(QUrl.fromLocalFile(path))
        self._play_btn.setEnabled(True)
        self._stop_btn.setEnabled(True)
        self._save_audio_btn.setEnabled(True)

    def _on_play_pause(self):
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _on_stop(self):
        self._player.stop()

    def _on_seek(self, position: int):
        self._player.setPosition(position)

    def _on_position_changed(self, position: int):
        self._seek_slider.blockSignals(True)
        self._seek_slider.setValue(position)
        self._seek_slider.blockSignals(False)
        self._time_label.setText(self._format_time(position))

    def _on_duration_changed(self, duration: int):
        self._seek_slider.setRange(0, duration)
        self._duration_label.setText(self._format_time(duration))

    def _on_playback_state(self, state):
        if state == QMediaPlayer.PlayingState:
            self._play_btn.setText("⏸  Pause")
        else:
            self._play_btn.setText("▶  Play")

    @staticmethod
    def _format_time(ms: int) -> str:
        """Format milliseconds as M:SS."""
        s = ms // 1000
        return f"{s // 60}:{s % 60:02d}"

    # ── Export ──────────────────────────────────────────────────

    def _copy_script(self):
        text = self._script_view.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def _save_audio(self):
        if not self._current_audio_path:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Narration Audio", "narration.wav",
            "WAV Audio (*.wav);;All Files (*)"
        )
        if path:
            import shutil
            shutil.copy2(self._current_audio_path, path)
