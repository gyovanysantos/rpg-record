"""
Pipeline Worker — runs the post-recording processing in a background QThread.

Steps: process (silence strip) → transcribe → merge → summarize
Each step emits progress signals so the UI can show status updates.
"""

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from processor import process_session
from transcriber import transcribe_session
from merger import merge_transcripts
from summarizer import summarize_session


class PipelineWorker(QObject):
    """
    Runs the full post-recording pipeline in a background thread.

    Signals:
        step_started(str): name of the current step
        step_finished(str, str): step name + result info
        pipeline_finished(str): path to final summary file
        error_occurred(str): if any step fails
    """

    step_started = Signal(str)
    step_finished = Signal(str, str)
    pipeline_finished = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, session_dir: str, num_channels: int = 1, parent=None):
        super().__init__(parent)
        self._session_dir = session_dir
        self._num_channels = num_channels

    def run(self):
        """Execute all pipeline steps sequentially."""
        session = Path(self._session_dir)

        from config import get_active_players
        players_map = get_active_players(self._num_channels)

        try:
            # Step 1: Process (silence stripping)
            self.step_started.emit("Processing audio...")
            stats = process_session(session)
            self.step_finished.emit("Processing", f"{len(stats)} channel(s) processed")

            # Step 2: Transcribe
            self.step_started.emit("Transcribing audio...")
            transcripts = transcribe_session(session, players_map)
            self.step_finished.emit("Transcription", f"{len(transcripts)} transcript(s)")

            # Step 3: Merge
            self.step_started.emit("Merging transcripts...")
            merged = merge_transcripts(session, players_map)
            self.step_finished.emit("Merge", str(merged))

            # Step 4: Summarize
            self.step_started.emit("Generating summary...")
            summary = summarize_session(session)
            self.step_finished.emit("Summary", str(summary))

            self.pipeline_finished.emit(str(summary))

        except Exception as e:
            self.error_occurred.emit(f"Pipeline error: {e}")


class PipelineThread(QThread):
    """
    Convenience wrapper — creates a QThread with PipelineWorker inside.

    Usage:
        thread = PipelineThread(session_dir="/path/to/session")
        thread.worker.step_started.connect(...)
        thread.worker.pipeline_finished.connect(...)
        thread.start()
    """

    def __init__(self, session_dir: str, num_channels: int = 1, parent=None):
        super().__init__(parent)
        self.worker = PipelineWorker(session_dir, num_channels)

    def run(self):
        self.worker.run()
