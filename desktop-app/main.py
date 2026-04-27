"""
Shadow of the Demon Lord — RPG Desktop App
Entry point: loads theme, shows role picker, launches main window.

Usage:
    python main.py
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# When running from source, add the repo root to sys.path so we can
# import recorder.py, config.py, etc. from the parent folder.
# When frozen (PyInstaller .exe), those modules are already bundled.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent
    REPO_ROOT = BASE_DIR.parent
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

from app.ui.role_picker import RolePickerDialog
from app.ui.main_window import MainWindow
STYLESHEET = BASE_DIR / "assets" / "styles" / "dark_fantasy.qss"


def load_stylesheet() -> str:
    """Read the QSS file and return its contents."""
    if STYLESHEET.exists():
        return STYLESHEET.read_text(encoding="utf-8")
    print(f"[WARN] Stylesheet not found: {STYLESHEET}")
    return ""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Shadow of the Demon Lord")
    app.setOrganizationName("RPG Record")

    # Apply dark fantasy theme
    qss = load_stylesheet()
    if qss:
        app.setStyleSheet(qss)

    # Role picker — user chooses DM or Player
    picker = RolePickerDialog()
    if picker.exec() != RolePickerDialog.Accepted:
        sys.exit(0)  # User closed the dialog

    role = picker.chosen_role()

    # Main window
    window = MainWindow(role)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
