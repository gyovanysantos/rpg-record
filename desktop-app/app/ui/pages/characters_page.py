"""
Characters Page — SotDL character sheet management.

Shows a character list with New/Delete buttons.
Double-click or select + Open to edit in a separate window.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QMessageBox,
)
from PySide6.QtCore import Qt

from app.models.character import (
    Character, save_character, load_character, list_characters,
)
from app.ui.dialogs.character_sheet_dialog import CharacterSheetDialog


class CharactersPage(QWidget):
    """Character sheet management — list + open in separate window."""

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._build_ui()
        self._refresh_list()

    # ── UI Construction ─────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("🧙  Character Sheets")
        title.setObjectName("heading")
        layout.addWidget(title)

        subtitle = QLabel("Double-click a character to open their sheet, or create a new one.")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        # Character list
        self._char_list = QListWidget()
        self._char_list.setMinimumHeight(300)
        self._char_list.setStyleSheet("QListWidget::item { padding: 8px; font-size: 15px; }")
        self._char_list.itemDoubleClicked.connect(self._open_character)
        layout.addWidget(self._char_list, stretch=1)

        # Buttons
        btn_row = QHBoxLayout()

        new_btn = QPushButton("✚ New Character")
        new_btn.setObjectName("primary")
        new_btn.setMinimumHeight(36)
        new_btn.clicked.connect(self._new_character)
        btn_row.addWidget(new_btn)

        open_btn = QPushButton("📝 Open Sheet")
        open_btn.setMinimumHeight(36)
        open_btn.clicked.connect(self._open_selected)
        btn_row.addWidget(open_btn)

        del_btn = QPushButton("🗑 Delete")
        del_btn.setObjectName("danger")
        del_btn.setMinimumHeight(36)
        del_btn.clicked.connect(self._delete_character)
        btn_row.addWidget(del_btn)

        layout.addLayout(btn_row)

    # ── Character List ──────────────────────────────────────────

    def _refresh_list(self):
        self._char_list.clear()
        for name, path in list_characters():
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, str(path))
            self._char_list.addItem(item)

    def _new_character(self):
        char = Character(name="New Hero")
        path = save_character(char)
        self._refresh_list()
        # Select and open the new character
        for i in range(self._char_list.count()):
            if self._char_list.item(i).data(Qt.UserRole) == str(path):
                self._char_list.setCurrentRow(i)
                self._open_character(self._char_list.item(i))
                break

    def _open_selected(self):
        item = self._char_list.currentItem()
        if not item:
            QMessageBox.information(self, "No Character Selected",
                                    "Select a character from the list first, or click '✚ New Character'.")
            return
        self._open_character(item)

    def _open_character(self, item: QListWidgetItem):
        path = Path(item.data(Qt.UserRole))
        if not path.exists():
            QMessageBox.warning(self, "Not Found", "Character file not found.")
            self._refresh_list()
            return
        char = load_character(path)
        dialog = CharacterSheetDialog(char, path, parent=self)
        dialog.character_saved.connect(self._refresh_list)
        dialog.exec()
        # Refresh after close in case name changed
        self._refresh_list()

    def _delete_character(self):
        item = self._char_list.currentItem()
        if not item:
            return
        path = Path(item.data(Qt.UserRole))
        if not path.exists():
            self._refresh_list()
            return
        char = load_character(path)
        reply = QMessageBox.question(
            self, "Delete Character",
            f"Delete '{char.name}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            path.unlink()
            self._refresh_list()
