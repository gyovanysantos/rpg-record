"""
Stub pages — placeholders for each section of the app.

Each page is a simple QWidget with a title and description.
They will be replaced with full implementations in later phases:
  Phase 2: RecorderPage
  Phase 3: DashboardPage
  Phase 4: CharactersPage
  Phase 5: InitiativePage, DicePage
  Phase 6: TranscriptPage
  Phase 7: NarratorPage
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


def _make_stub(title: str, description: str, phase: str) -> QWidget:
    """Create a placeholder page widget."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(32, 32, 32, 32)
    layout.setSpacing(16)

    heading = QLabel(title)
    heading.setObjectName("heading")
    heading.setAlignment(Qt.AlignLeft)
    layout.addWidget(heading)

    desc = QLabel(description)
    desc.setObjectName("subheading")
    desc.setWordWrap(True)
    layout.addWidget(desc)

    phase_label = QLabel(f"Coming in {phase}")
    phase_label.setObjectName("muted")
    layout.addWidget(phase_label)

    layout.addStretch()
    return page


class DashboardPage(QWidget):
    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        stub = _make_stub(
            "🏠  Campaign Dashboard",
            "View your campaign overview, session history, and quick stats.",
            "Phase 3",
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(stub)


class RecorderPage(QWidget):
    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        stub = _make_stub(
            "🎙️  Session Recorder",
            "Record your RPG session with multi-channel audio, live levels, and automatic transcription.",
            "Phase 2",
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(stub)


class NarratorPage(QWidget):
    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        stub = _make_stub(
            "🔊  Cinematic Narrator",
            "Gemini TTS-powered dramatic narration of session recaps with multi-speaker voices.",
            "Phase 7",
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(stub)
