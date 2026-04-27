"""
Update Checker — non-blocking check for newer app versions on launch.

How it works:
1. A QThread fetches a small JSON file from a public URL (GitHub Gist)
2. Compares the remote version against the local __version__
3. If a newer version exists, emits `update_available` with the details
4. If the check fails (no internet, etc.), it silently does nothing

The Gist URL must contain JSON like:
    {"version": "0.2.0", "download_url": "https://...", "notes": "Bug fixes..."}

To set up your Gist:
1. Go to https://gist.github.com
2. Create a public gist named "rpg-record-version.json"
3. Paste: {"version": "0.1.0", "download_url": "", "notes": "Initial release"}
4. Copy the RAW URL and paste it into UPDATE_URL below
"""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, QThread

from app.__version__ import __version__

# ── Configuration ───────────────────────────────────────────────
# Replace this with your actual Gist raw URL after creating the Gist.
# Format: https://gist.githubusercontent.com/<user>/<gist_id>/raw/rpg-record-version.json
UPDATE_URL = ""

# How long to wait for the server (seconds)
_TIMEOUT = 5


# ── Data ────────────────────────────────────────────────────────

@dataclass
class UpdateInfo:
    """Info about an available update."""
    current_version: str
    latest_version: str
    download_url: str
    notes: str


# ── Version comparison ──────────────────────────────────────────

def _parse_version(v: str) -> tuple[int, ...]:
    """Parse '1.2.3' into (1, 2, 3) for comparison."""
    try:
        return tuple(int(x) for x in v.strip().lstrip("v").split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _is_newer(remote: str, local: str) -> bool:
    """Return True if remote version is strictly newer than local."""
    return _parse_version(remote) > _parse_version(local)


# ── Worker ──────────────────────────────────────────────────────

class UpdateWorker(QObject):
    """Background worker that checks for updates."""

    update_available = Signal(object)  # emits UpdateInfo
    finished = Signal()

    def run(self):
        """Fetch version info and compare. Fails silently."""
        try:
            if not UPDATE_URL:
                return

            req = urllib.request.Request(
                UPDATE_URL,
                headers={"User-Agent": "SotDL-RPG-Recorder"},
            )
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            remote_version = data.get("version", "")
            if remote_version and _is_newer(remote_version, __version__):
                info = UpdateInfo(
                    current_version=__version__,
                    latest_version=remote_version,
                    download_url=data.get("download_url", ""),
                    notes=data.get("notes", ""),
                )
                self.update_available.emit(info)
        except Exception:
            pass  # Network errors, JSON errors — all silently ignored
        finally:
            self.finished.emit()


# ── Convenience launcher ────────────────────────────────────────

def check_for_updates(parent: QObject, callback):
    """
    Launch a background update check. Non-blocking.

    Usage in MainWindow.__init__:
        from app.core.update_checker import check_for_updates
        check_for_updates(self, self._on_update_available)

    Args:
        parent: QObject to own the thread (prevents GC).
        callback: Slot that receives an UpdateInfo object.
    """
    if not UPDATE_URL:
        return  # No URL configured — skip silently

    thread = QThread(parent)
    worker = UpdateWorker()
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.update_available.connect(callback)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    # Store references to prevent garbage collection
    parent._update_thread = thread
    parent._update_worker = worker

    thread.start()
