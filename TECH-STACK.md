# RPG Session Recorder — Tech Stack

## Python 3.12+
**Why:** Primary language. Modern features, strong ecosystem for audio/AI tasks.

## sounddevice 0.5.5
**Why:** Cross-platform audio I/O built on PortAudio. Supports multi-channel recording, device enumeration, and real-time audio level monitoring. Chosen over `pyaudio` for its cleaner API and numpy integration.

## scipy 1.17.1
**Why:** Used for `scipy.io.wavfile.write()` to save raw audio data (numpy arrays) as `.wav` files. Lightweight and doesn't require ffmpeg for basic wav I/O.

## numpy 2.3.3
**Why:** Audio data is handled as numpy arrays throughout the recording pipeline. Required by both `sounddevice` and `scipy`.

## pydub 0.25.1
**Why:** High-level audio manipulation library. Used specifically for `pydub.silence.split_on_silence()` to strip silence from recordings. Simple API for audio segmentation without writing DSP code.

> **Requires ffmpeg:** pydub depends on ffmpeg for audio format handling.
> Install on Windows: `choco install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html).

## groq 1.2.0
**Why:** Official Python SDK for Groq API. Used to access Whisper Large V3 for fast, accurate speech-to-text transcription with timestamps. Groq's inference speed makes it practical for transcribing multi-channel sessions.

## anthropic 0.84.0
**Why:** Official Python SDK for Anthropic API. Used to send merged transcripts to Claude for generating structured RPG session summaries (narrative, timeline, lore, character moments, cliffhangers).

## gradio 6.13.0
**Why:** Rapid UI framework for Python. Provides device selector dropdowns, buttons, text displays, and real-time updates with minimal frontend code. Ideal for a desktop tool that doesn't need a full web framework.

## python-dotenv 1.1.0
**Why:** Loads API keys from `.env` file into environment variables. Keeps secrets out of source code and `.env` is git-ignored.

## ffmpeg 8.1 (system dependency)
**Why:** Required by pydub for audio format handling (encoding/decoding). Must be installed separately on the system.
- **Windows:** `winget install --id Gyan.FFmpeg` (recommended) or `choco install ffmpeg`
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

---

# Desktop App — Additional Dependencies

## PySide6 6.11.0
**Why:** Qt for Python — the desktop UI framework. Chosen over Tkinter (too basic), PyQt6 (GPL licensing concerns), and Electron (too heavy). PySide6 provides deep QSS theming (CSS-like), QtMultimedia for audio, signals/slots architecture, QThread for background work, and first-class support for PyInstaller `.exe` packaging.

## PyInstaller 6.0+
**Why:** Bundles the entire Python app + PySide6 + assets into a standalone Windows `.exe`. No Python installation needed on the end user's machine. Configured via `build.spec` in `desktop-app/`.

## google-genai 1.73.1
**Why:** Official Google Gen AI Python SDK. Used for Gemini TTS (text-to-speech) to generate cinematic narration audio from session summaries. Two-step pipeline: (1) Gemini text model transforms summaries into dramatic scripts, (2) Gemini TTS model (`gemini-2.5-flash-preview-tts`) converts scripts to WAV audio with configurable voices and styles. Supports 30 prebuilt voices, audio style tags, and advanced prompting with scene/director/character profiles.
