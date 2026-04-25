"""
Settings Page — configure API keys and model selection for each AI service.

Each AI service gets a card with:
- Service name and description
- API key input (masked, with show/hide toggle)
- Model dropdown
- Connection test button

Changes are saved to the .env file and immediately available to all modules.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QComboBox, QLineEdit, QScrollArea,
    QMessageBox, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.core.settings_manager import (
    AI_SERVICES, get_setting, save_all,
)


class _ServiceCard(QGroupBox):
    """A card for one AI service — key input, model picker, description."""

    def __init__(self, service_id: str, info: dict, parent=None):
        super().__init__(info["label"], parent)
        self.setObjectName("card")
        self._service_id = service_id
        self._info = info
        self._build_ui()
        self._load_current()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ── Description ──
        desc = QLabel(self._info["description"])
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # ── API Key row ──
        key_row = QHBoxLayout()
        key_label = QLabel("API Key:")
        key_label.setFixedWidth(80)
        key_row.addWidget(key_label)

        self._key_input = QLineEdit()
        self._key_input.setEchoMode(QLineEdit.Password)
        self._key_input.setPlaceholderText("Paste your API key here...")
        self._key_input.setMinimumHeight(36)
        key_row.addWidget(self._key_input, stretch=1)

        self._toggle_btn = QPushButton("👁")
        self._toggle_btn.setFixedSize(36, 36)
        self._toggle_btn.setToolTip("Show / hide key")
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle_visibility)
        key_row.addWidget(self._toggle_btn)

        self._test_btn = QPushButton("Test")
        self._test_btn.setObjectName("primary")
        self._test_btn.setFixedHeight(36)
        self._test_btn.setCursor(Qt.PointingHandCursor)
        self._test_btn.clicked.connect(self._test_connection)
        key_row.addWidget(self._test_btn)

        layout.addLayout(key_row)

        # ── Model row ──
        model_row = QHBoxLayout()
        model_label = QLabel("Model:")
        model_label.setFixedWidth(80)
        model_row.addWidget(model_label)

        self._model_combo = QComboBox()
        self._model_combo.setMinimumHeight(36)
        for model_id, description in self._info["models"]:
            self._model_combo.addItem(f"{model_id}  —  {description}", model_id)
        model_row.addWidget(self._model_combo, stretch=1)

        layout.addLayout(model_row)

        # ── Status label ──
        self._status = QLabel("")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

    def _load_current(self):
        """Load saved key and model into the UI."""
        key_env = self._info["key_env"]
        model_env = self._info["model_env"]

        current_key = get_setting(key_env)
        self._key_input.setText(current_key)

        current_model = get_setting(model_env, self._info["default_model"])
        for i in range(self._model_combo.count()):
            if self._model_combo.itemData(i) == current_model:
                self._model_combo.setCurrentIndex(i)
                break

    def _toggle_visibility(self):
        if self._key_input.echoMode() == QLineEdit.Password:
            self._key_input.setEchoMode(QLineEdit.Normal)
            self._toggle_btn.setText("🔒")
        else:
            self._key_input.setEchoMode(QLineEdit.Password)
            self._toggle_btn.setText("👁")

    def _test_connection(self):
        """Quick validation that the API key works."""
        key = self._key_input.text().strip()
        if not key:
            self._status.setText("❌  No API key entered.")
            self._status.setStyleSheet("color: #8b0000;")
            return

        self._status.setText("⏳  Testing...")
        self._status.setStyleSheet("color: #c4a35a;")
        self._status.repaint()

        try:
            if self._service_id == "groq":
                self._test_groq(key)
            elif self._service_id == "anthropic":
                self._test_anthropic(key)
            elif self._service_id == "gemini":
                self._test_gemini(key)
            self._status.setText("✅  Connection successful!")
            self._status.setStyleSheet("color: #2e5e3e;")
        except Exception as e:
            msg = str(e)
            if len(msg) > 200:
                msg = msg[:200] + "..."
            self._status.setText(f"❌  {msg}")
            self._status.setStyleSheet("color: #8b0000;")

    def _test_groq(self, key: str):
        from groq import Groq
        client = Groq(api_key=key)
        client.models.list()

    def _test_anthropic(self, key: str):
        from anthropic import Anthropic
        client = Anthropic(api_key=key)
        client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say OK"}],
        )

    def _test_gemini(self, key: str):
        from google import genai
        client = genai.Client(api_key=key)
        client.models.get(model="gemini-2.5-flash")

    def get_values(self) -> dict[str, str]:
        """Return {env_key: value} pairs for saving."""
        return {
            self._info["key_env"]: self._key_input.text().strip(),
            self._info["model_env"]: self._model_combo.currentData(),
        }


class SettingsPage(QWidget):
    """Settings page — API keys, model selection, and AI service configuration."""

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._cards: list[_ServiceCard] = []
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # ── Scrollable area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ── Header ──
        title = QLabel("⚙️  Settings")
        title.setObjectName("heading")
        title_font = QFont()
        title_font.setPointSize(22)
        title.setFont(title_font)
        layout.addWidget(title)

        subtitle = QLabel(
            "Configure your AI services below. API keys are stored locally "
            "in your .env file and never sent anywhere except to the respective API."
        )
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # ── Service cards ──
        for service_id, info in AI_SERVICES.items():
            card = _ServiceCard(service_id, info)
            self._cards.append(card)
            layout.addWidget(card)

        layout.addSpacing(8)

        # ── Save button ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._save_btn = QPushButton("💾  Save All Settings")
        self._save_btn.setObjectName("primary")
        self._save_btn.setMinimumHeight(44)
        self._save_btn.setMinimumWidth(220)
        self._save_btn.setCursor(Qt.PointingHandCursor)
        save_font = QFont()
        save_font.setPointSize(13)
        self._save_btn.setFont(save_font)
        self._save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self._save_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()
        scroll.setWidget(container)

        # ── Status bar ──
        self._save_status = QLabel("")
        self._save_status.setAlignment(Qt.AlignCenter)
        outer.addWidget(self._save_status)

    def _on_save(self):
        """Collect all values and save to .env."""
        all_settings = {}
        for card in self._cards:
            all_settings.update(card.get_values())

        save_all(all_settings)

        self._save_status.setText("✅  Settings saved successfully!")
        self._save_status.setStyleSheet("color: #2e5e3e; padding: 8px;")
