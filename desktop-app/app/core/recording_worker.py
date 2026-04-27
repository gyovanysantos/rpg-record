"""
Recording Worker — QThread wrapper around the existing Recorder module.

Runs the audio recording in a background thread so the UI stays responsive.
Emits signals for:
  - levels_updated(list[float]): RMS levels per channel, polled via QTimer
  - recording_finished(list[str]): file paths of saved .wav files
  - error_occurred(str): if something goes wrong
"""

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Signal

# When running from source, add repo root to import original modules.
# When frozen (PyInstaller .exe), those modules are already bundled.
if not getattr(sys, "frozen", False):
    _REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

from recorder import Recorder, list_devices, select_device
from config import get_session_dir, get_active_players, SAMPLE_RATE


class RecordingWorker(QObject):
    """
    Manages audio recording lifecycle in a way that's safe for Qt.

    This is NOT a QThread itself — it lives on the main thread and uses
    QTimer to poll levels. The actual Recorder uses sounddevice's own
    callback thread internally, so we don't need a separate QThread
    for the recording itself.

    Usage:
        worker = RecordingWorker()
        worker.levels_updated.connect(ui.update_meters)
        worker.recording_finished.connect(ui.on_recording_done)
        worker.start_recording(device_index=0, num_channels=1)
        # ... later ...
        worker.stop_recording()
    """

    levels_updated = Signal(list)           # [float, float, ...] per channel
    recording_finished = Signal(list)       # [str, str, ...] saved file paths
    recording_started = Signal(str)         # session_dir path
    error_occurred = Signal(str)            # error message
    elapsed_updated = Signal(int)           # seconds elapsed

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recorder: Recorder | None = None
        self._session_dir: Path | None = None
        self._elapsed_seconds = 0

        # Timer to poll RMS levels from the recorder (~20 fps)
        self._level_timer = QTimer(self)
        self._level_timer.setInterval(50)  # 50ms = 20 Hz
        self._level_timer.timeout.connect(self._poll_levels)

        # Timer to track elapsed recording time
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._tick_clock)

    # ── Public API ──────────────────────────────────────────────

    def start_recording(self, device_index: int | None, num_channels: int):
        """Begin recording from the specified device."""
        try:
            self._session_dir = get_session_dir()
            self._recorder = Recorder(
                device_index=device_index,
                num_channels=num_channels,
                sample_rate=SAMPLE_RATE,
            )
            self._recorder.start(self._session_dir)
            self._elapsed_seconds = 0
            self._level_timer.start()
            self._clock_timer.start()
            self.recording_started.emit(str(self._session_dir))
        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop_recording(self):
        """Stop recording and save files."""
        try:
            self._level_timer.stop()
            self._clock_timer.stop()
            if self._recorder and self._recorder.is_recording:
                saved_files = self._recorder.stop()
                file_strs = [str(f) for f in saved_files]
                self.recording_finished.emit(file_strs)
            self._recorder = None
        except Exception as e:
            self.error_occurred.emit(str(e))

    @property
    def is_recording(self) -> bool:
        return self._recorder is not None and self._recorder.is_recording

    @property
    def session_dir(self) -> Path | None:
        return self._session_dir

    # ── Internal ────────────────────────────────────────────────

    def _poll_levels(self):
        """Read current RMS levels and emit signal."""
        if self._recorder and self._recorder.is_recording:
            levels = self._recorder.get_levels()
            self.levels_updated.emit(levels)

    def _tick_clock(self):
        """Increment elapsed time counter."""
        self._elapsed_seconds += 1
        self.elapsed_updated.emit(self._elapsed_seconds)
