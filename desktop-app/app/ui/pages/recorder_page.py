"""
Recorder Page — full session recording UI (DM only).

Layout:
┌────────────────────────────────────────────────────────┐
│  🎙️  Session Recorder                                  │
│                                                        │
│  Device: [dropdown]    Channels: [1 ▼]                 │
│                                                        │
│  ┌─ Player Cards ────────────────────────────────────┐ │
│  │ CH 0 — Dungeon Master  [████████░░░]              │ │
│  │ CH 1 — Player 1        [██████░░░░░]              │ │
│  │ ...                                               │ │
│  └───────────────────────────────────────────────────┘ │
│                                                        │
│  [● Record]  [■ Stop]      00:00:00    📁 session/... │
│                                                        │
│  ── Post-Recording Pipeline ──                         │
│  [▶ Process & Transcribe]   Status: Idle               │
└────────────────────────────────────────────────────────┘
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QFrame, QGroupBox, QScrollArea,
)
from PySide6.QtCore import Qt

# When running from source, add repo root for importing original modules.
# When frozen (PyInstaller .exe), those modules are already bundled.
if not getattr(sys, "frozen", False):
    _REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

from recorder import list_devices
from config import get_active_players

from app.core.recording_worker import RecordingWorker
from app.core.pipeline_worker import PipelineThread
from app.ui.widgets.player_card import PlayerCard


class RecorderPage(QWidget):
    """Full recording page with device selection, level meters, and pipeline."""

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._player_cards: list[PlayerCard] = []
        self._recording_worker = RecordingWorker(self)
        self._pipeline_thread: PipelineThread | None = None

        self._build_ui()
        self._connect_signals()
        self._refresh_devices()
        self._rebuild_player_cards()

    # ── UI Construction ─────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("🎙️  Session Recorder")
        title.setObjectName("heading")
        layout.addWidget(title)

        # ── Device & Channel Selection ──
        config_row = QHBoxLayout()
        config_row.setSpacing(16)

        # Device dropdown
        config_row.addWidget(QLabel("Audio Device:"))
        self._device_combo = QComboBox()
        self._device_combo.setMinimumWidth(300)
        config_row.addWidget(self._device_combo, stretch=1)

        # Refresh button
        self._refresh_btn = QPushButton("↻")
        self._refresh_btn.setFixedWidth(36)
        self._refresh_btn.setToolTip("Refresh device list")
        self._refresh_btn.clicked.connect(self._refresh_devices)
        config_row.addWidget(self._refresh_btn)

        # Channel count
        config_row.addSpacing(16)
        config_row.addWidget(QLabel("Channels:"))
        self._channel_spin = QSpinBox()
        self._channel_spin.setRange(1, 8)
        self._channel_spin.setValue(1)
        self._channel_spin.setToolTip("1 for laptop mic, 5 for Focusrite Scarlett 6i6")
        self._channel_spin.valueChanged.connect(self._rebuild_player_cards)
        config_row.addWidget(self._channel_spin)

        layout.addLayout(config_row)

        # ── Player Cards (inside a scroll area) ──
        cards_group = QGroupBox("Player Channels")
        self._cards_layout = QVBoxLayout(cards_group)
        self._cards_layout.setSpacing(6)
        layout.addWidget(cards_group)

        # ── Recording Controls ──
        controls_row = QHBoxLayout()
        controls_row.setSpacing(12)

        self._record_btn = QPushButton("●  Record")
        self._record_btn.setObjectName("danger")
        self._record_btn.setCursor(Qt.PointingHandCursor)
        self._record_btn.clicked.connect(self._on_record)
        controls_row.addWidget(self._record_btn)

        self._stop_btn = QPushButton("■  Stop")
        self._stop_btn.setEnabled(False)
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.clicked.connect(self._on_stop)
        controls_row.addWidget(self._stop_btn)

        controls_row.addSpacing(24)

        # Elapsed time display
        self._time_label = QLabel("00:00:00")
        self._time_label.setObjectName("subheading")
        self._time_label.setFixedWidth(100)
        controls_row.addWidget(self._time_label)

        controls_row.addStretch()

        # Session directory display
        self._session_label = QLabel("")
        self._session_label.setObjectName("muted")
        controls_row.addWidget(self._session_label)

        layout.addLayout(controls_row)

        # ── Post-Recording Pipeline ──
        pipeline_group = QGroupBox("Post-Recording Pipeline")
        pipeline_layout = QVBoxLayout(pipeline_group)

        pipeline_row = QHBoxLayout()

        self._pipeline_btn = QPushButton("▶  Process & Transcribe")
        self._pipeline_btn.setObjectName("primary")
        self._pipeline_btn.setEnabled(False)
        self._pipeline_btn.setCursor(Qt.PointingHandCursor)
        self._pipeline_btn.clicked.connect(self._on_pipeline)
        pipeline_row.addWidget(self._pipeline_btn)

        pipeline_row.addSpacing(16)

        self._pipeline_status = QLabel("Status: Idle")
        self._pipeline_status.setObjectName("muted")
        pipeline_row.addWidget(self._pipeline_status, stretch=1)

        pipeline_layout.addLayout(pipeline_row)

        # Pipeline log area
        self._pipeline_log = QLabel("")
        self._pipeline_log.setObjectName("muted")
        self._pipeline_log.setWordWrap(True)
        pipeline_layout.addWidget(self._pipeline_log)

        layout.addWidget(pipeline_group)

        layout.addStretch()

    # ── Signal Wiring ───────────────────────────────────────────

    def _connect_signals(self):
        w = self._recording_worker
        w.levels_updated.connect(self._on_levels)
        w.recording_started.connect(self._on_recording_started)
        w.recording_finished.connect(self._on_recording_finished)
        w.elapsed_updated.connect(self._on_elapsed)
        w.error_occurred.connect(self._on_error)

    # ── Device Management ───────────────────────────────────────

    def _refresh_devices(self):
        """Re-scan audio devices and populate the dropdown."""
        self._device_combo.clear()
        self._device_combo.addItem("System Default", None)
        try:
            devices = list_devices()
            for dev in devices:
                label = f"[{dev['index']}] {dev['name']} ({dev['max_channels']}ch)"
                self._device_combo.addItem(label, dev["index"])
        except Exception as e:
            self._device_combo.addItem(f"Error: {e}", None)

    # ── Player Cards ────────────────────────────────────────────

    def _rebuild_player_cards(self):
        """Recreate player cards based on current channel count."""
        # Clear existing cards
        for card in self._player_cards:
            self._cards_layout.removeWidget(card)
            card.deleteLater()
        self._player_cards.clear()

        # Build new cards
        num_ch = self._channel_spin.value()
        players = get_active_players(num_ch)

        for i in range(num_ch):
            name = players.get(f"channel_{i}", f"Channel {i}")
            card = PlayerCard(channel=i, player_name=name)
            self._cards_layout.addWidget(card)
            self._player_cards.append(card)

    # ── Recording Slots ─────────────────────────────────────────

    def _on_record(self):
        device_index = self._device_combo.currentData()
        num_channels = self._channel_spin.value()
        self._recording_worker.start_recording(device_index, num_channels)

    def _on_stop(self):
        self._recording_worker.stop_recording()

    def _on_recording_started(self, session_dir: str):
        self._record_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._device_combo.setEnabled(False)
        self._channel_spin.setEnabled(False)
        self._pipeline_btn.setEnabled(False)
        self._session_label.setText(f"📁 {Path(session_dir).name}")
        self._time_label.setText("00:00:00")

    def _on_recording_finished(self, file_paths: list[str]):
        self._record_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._device_combo.setEnabled(True)
        self._channel_spin.setEnabled(True)
        self._pipeline_btn.setEnabled(True)

        # Reset all meters
        for card in self._player_cards:
            card.reset()

        count = len(file_paths)
        self._session_label.setText(
            f"📁 {Path(file_paths[0]).parent.parent.name} — {count} file(s) saved"
            if file_paths else "No files saved"
        )

    def _on_levels(self, levels: list[float]):
        """Update player card level meters."""
        for i, level in enumerate(levels):
            if i < len(self._player_cards):
                # Scale RMS to a more visible range (raw RMS is often 0.0–0.1)
                scaled = min(1.0, level * 5.0)
                self._player_cards[i].set_level(scaled)

    def _on_elapsed(self, seconds: int):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        self._time_label.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _on_error(self, msg: str):
        self._pipeline_status.setText(f"⚠️ Error: {msg}")
        self._record_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._device_combo.setEnabled(True)
        self._channel_spin.setEnabled(True)

    # ── Pipeline Slots ──────────────────────────────────────────

    def _on_pipeline(self):
        session_dir = self._recording_worker.session_dir
        if not session_dir:
            self._pipeline_status.setText("⚠️ No session to process")
            return

        self._pipeline_btn.setEnabled(False)
        self._pipeline_log.setText("")
        self._pipeline_status.setText("Status: Running...")

        num_channels = self._channel_spin.value()
        self._pipeline_thread = PipelineThread(str(session_dir), num_channels, parent=self)
        self._pipeline_thread.worker.step_started.connect(self._on_step_started)
        self._pipeline_thread.worker.step_finished.connect(self._on_step_finished)
        self._pipeline_thread.worker.pipeline_finished.connect(self._on_pipeline_done)
        self._pipeline_thread.worker.error_occurred.connect(self._on_pipeline_error)
        self._pipeline_thread.finished.connect(self._pipeline_thread.deleteLater)
        self._pipeline_thread.start()

    def _on_step_started(self, step: str):
        self._pipeline_status.setText(f"Status: {step}")

    def _on_step_finished(self, step: str, info: str):
        current = self._pipeline_log.text()
        self._pipeline_log.setText(f"{current}\n✅ {step}: {info}".strip())

    def _on_pipeline_done(self, summary_path: str):
        self._pipeline_status.setText("Status: ✅ Complete!")
        self._pipeline_btn.setEnabled(True)
        current = self._pipeline_log.text()
        self._pipeline_log.setText(
            f"{current}\n\n📄 Summary saved to: {Path(summary_path).name}"
        )

    def _on_pipeline_error(self, msg: str):
        self._pipeline_status.setText(f"⚠️ {msg}")
        self._pipeline_btn.setEnabled(True)
