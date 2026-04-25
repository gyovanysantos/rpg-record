"""
recorder.py — Multi-channel audio recording module.

Uses sounddevice to record from any audio input device.
Supports 1 channel (laptop mic) or 5 channels (Focusrite Scarlett 6i6).
Each channel is saved as a separate .wav file.
"""

import queue
import threading
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from pathlib import Path

from config import SAMPLE_RATE, NUM_CHANNELS, AUDIO_DEVICE


def list_devices() -> list[dict]:
    """
    List all available audio input devices.

    Returns:
        List of dicts with keys: index, name, max_channels.
        Only devices with at least 1 input channel are included.
    """
    devices = sd.query_devices()
    input_devices = []
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            input_devices.append({
                "index": i,
                "name": dev["name"],
                "max_channels": dev["max_input_channels"],
            })
    return input_devices


def select_device(device_index: int) -> dict:
    """
    Validate and return info about a specific audio device.

    Args:
        device_index: Index of the device from sounddevice.query_devices().

    Returns:
        Dict with device info (index, name, max_channels).

    Raises:
        ValueError: If device doesn't exist or has no input channels.
    """
    try:
        dev = sd.query_devices(device_index)
    except sd.PortAudioError:
        raise ValueError(f"Device index {device_index} not found.")

    if dev["max_input_channels"] < 1:
        raise ValueError(f"Device '{dev['name']}' has no input channels.")

    return {
        "index": device_index,
        "name": dev["name"],
        "max_channels": dev["max_input_channels"],
    }


class Recorder:
    """
    Multi-channel audio recorder.

    Records audio from a selected device into a buffer,
    computes live RMS levels per channel, and saves each
    channel as a separate .wav file on stop.

    Usage:
        rec = Recorder(device_index=0, num_channels=1, sample_rate=44100)
        rec.start(session_dir=Path("sessions/2026-04-25"))
        levels = rec.get_levels()   # poll for UI meters
        files = rec.stop()          # returns list of saved .wav paths
    """

    def __init__(
        self,
        device_index: int | None = None,
        num_channels: int = NUM_CHANNELS,
        sample_rate: int = SAMPLE_RATE,
    ):
        """
        Initialize the recorder.

        Args:
            device_index: Audio device index (None = system default).
            num_channels: Number of channels to record (1 for laptop, 5 for Focusrite).
            sample_rate: Sample rate in Hz (default 44100).
        """
        self.device_index = device_index
        self.num_channels = num_channels
        self.sample_rate = sample_rate

        # Thread-safe queue for audio chunks
        self._audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        # Collected audio data (list of numpy arrays)
        self._recordings: list[np.ndarray] = []
        # Current RMS levels per channel (updated in real-time)
        self._current_levels: np.ndarray = np.zeros(num_channels)
        # Lock for thread-safe level access
        self._levels_lock = threading.Lock()
        # Stream reference
        self._stream: sd.InputStream | None = None
        # Recording state
        self._is_recording = False
        self._session_dir: Path | None = None

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """
        Called by sounddevice for each audio block.

        Stores audio data and computes RMS levels per channel.
        This runs in a separate thread — must be thread-safe.
        """
        if status:
            print(f"Audio callback status: {status}")

        # Copy data to avoid reference issues (sounddevice reuses buffer)
        data = indata.copy()
        self._audio_queue.put(data)

        # Compute RMS per channel for level meters
        rms = np.sqrt(np.mean(data ** 2, axis=0))
        with self._levels_lock:
            self._current_levels = rms

    def start(self, session_dir: Path) -> None:
        """
        Start recording audio.

        Args:
            session_dir: Path to the session directory (must have a raw/ subdirectory).

        Raises:
            RuntimeError: If already recording.
        """
        if self._is_recording:
            raise RuntimeError("Already recording. Call stop() first.")

        self._session_dir = session_dir
        raw_dir = session_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)

        # Clear previous data
        self._recordings.clear()
        while not self._audio_queue.empty():
            self._audio_queue.get()

        # Open audio stream
        self._stream = sd.InputStream(
            device=self.device_index,
            channels=self.num_channels,
            samplerate=self.sample_rate,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()
        self._is_recording = True
        print(f"Recording started: {self.num_channels} channel(s) at {self.sample_rate} Hz")

    def get_levels(self) -> list[float]:
        """
        Get current RMS audio levels per channel.

        Returns:
            List of RMS values (0.0 to 1.0) for each channel.
            Used by the UI to display live level meters.
        """
        with self._levels_lock:
            return self._current_levels.tolist()

    def stop(self) -> list[Path]:
        """
        Stop recording and save each channel as a separate .wav file.

        Returns:
            List of Paths to the saved .wav files (one per channel).

        Raises:
            RuntimeError: If not currently recording.
        """
        if not self._is_recording:
            raise RuntimeError("Not currently recording.")

        # Stop the stream
        self._stream.stop()
        self._stream.close()
        self._stream = None
        self._is_recording = False

        # Drain the queue into recordings list
        while not self._audio_queue.empty():
            self._recordings.append(self._audio_queue.get())

        if not self._recordings:
            print("Warning: No audio data recorded.")
            return []

        # Concatenate all chunks into one big array: shape (total_samples, num_channels)
        all_audio = np.concatenate(self._recordings, axis=0)
        print(f"Recording stopped. Total samples: {all_audio.shape[0]}, "
              f"Duration: {all_audio.shape[0] / self.sample_rate:.1f}s")

        # Split into per-channel files and save
        raw_dir = self._session_dir / "raw"
        saved_files = []

        for ch in range(self.num_channels):
            # Extract single channel
            if self.num_channels == 1:
                channel_data = all_audio.flatten()
            else:
                channel_data = all_audio[:, ch]

            # Convert float32 [-1.0, 1.0] to int16 for .wav
            channel_int16 = np.clip(channel_data * 32767, -32768, 32767).astype(np.int16)

            # Save as .wav
            filepath = raw_dir / f"channel_{ch}.wav"
            wavfile.write(str(filepath), self.sample_rate, channel_int16)
            saved_files.append(filepath)
            print(f"  Saved: {filepath}")

        return saved_files

    @property
    def is_recording(self) -> bool:
        """Whether the recorder is currently active."""
        return self._is_recording


# --- Standalone test ---
if __name__ == "__main__":
    import time
    from config import get_session_dir

    print("=== Recorder Module Test ===\n")

    # List available devices
    print("Available input devices:")
    devices = list_devices()
    for d in devices:
        print(f"  [{d['index']}] {d['name']} ({d['max_channels']} ch)")

    if not devices:
        print("No input devices found!")
        exit(1)

    # Use default device, 1 channel (laptop mode)
    print(f"\nRecording 5 seconds from default device (1 channel)...")
    session_dir = get_session_dir()
    print(f"Session directory: {session_dir}")

    rec = Recorder(device_index=None, num_channels=1, sample_rate=44100)
    rec.start(session_dir)

    # Poll levels for 5 seconds
    for i in range(10):
        time.sleep(0.5)
        levels = rec.get_levels()
        bar = "█" * int(levels[0] * 50)
        print(f"  Level: {bar} ({levels[0]:.4f})")

    files = rec.stop()
    print(f"\nSaved {len(files)} file(s):")
    for f in files:
        print(f"  {f} ({f.stat().st_size / 1024:.1f} KB)")
