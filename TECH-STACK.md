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

---

# Distribution & CI/CD

## GitHub Actions
**Why:** Automated build-and-release pipeline. On `v*` tag push, builds the `.exe` on a Windows runner and creates a GitHub Release with the binary attached. No manual packaging needed — just tag and push.

## GitHub CLI (gh) 2.89.0
**Why:** Used during initial repo setup to create the remote repository and push. Also useful for checking releases from the command line.

## urllib (stdlib)
**Why:** Used in `update_checker.py` to fetch a remote `version.json` from a public GitHub Gist. No external HTTP library needed — stdlib keeps the dependency count low.

---

# Desktop App v2 — Tauri + React Stack

## Tauri v2 (Rust)
**Why:** Lightweight alternative to Electron. Uses the OS webview instead of bundling Chromium, resulting in ~10MB executables vs ~150MB for Electron. Native feel, low memory usage, Rust security. The shell plugin launches the FastAPI Python backend as a sidecar.

## React 18.3
**Why:** Component-based UI library. Industry standard, massive ecosystem, declarative rendering. Chosen over Vue/Svelte for broader community support and library availability (react-query, framer-motion, etc.).

## TypeScript 5.6
**Why:** Static typing for JavaScript. Catches bugs at compile time, better IDE support, self-documenting code. Essential for a project this size.

## Vite 6
**Why:** Next-gen frontend build tool. Sub-second HMR (hot module replacement), native ES modules in dev, fast production builds. Replaces webpack/CRA. Built-in proxy for routing `/api` calls to the FastAPI backend during development.

## TailwindCSS 3.4
**Why:** Utility-first CSS framework. Rapid prototyping with dark fantasy theme via custom color tokens. No separate CSS files needed — styles live in the component markup. Custom animations (card-flip, fade-in, glow) defined in config.

## zustand 5
**Why:** Minimal state management (1KB). Simpler than Redux, no boilerplate. Stores role selection and sidebar state with `persist` middleware for localStorage persistence.

## @tanstack/react-query 5
**Why:** Server state management. Handles caching, background refetching, loading/error states for all FastAPI calls. Eliminates manual `useEffect` + `useState` fetch patterns.

## framer-motion 11
**Why:** Production-ready animation library for React. Powers page transitions (fade+slide), card hover effects, and the dice roller animation. Declarative API with `AnimatePresence` for exit animations.

## react-i18next 15 + i18next 24
**Why:** Internationalization framework. The app defaults to PT-BR (user's language) with English toggle. Translation keys stored in JSON files (`locales/pt-BR.json`, `locales/en.json`). Language persisted in localStorage.

## lucide-react 0.460
**Why:** Modern icon set (1000+ icons). Consistent style, tree-shakeable (only imports used icons). Replaces icon fonts — each icon is an optimized SVG React component.

## react-router-dom 7
**Why:** Client-side routing for the SPA. Maps URL paths to page components. Supports role-based route filtering (DM-only pages like recorder, transcripts, narrator).

## FastAPI 0.115+
**Why:** Modern async Python web framework for the backend API. Auto-generates OpenAPI docs, Pydantic validation, async support. Wraps all existing Python modules (character, config, recorder, etc.) with REST endpoints. Runs on `localhost:8420`.

## uvicorn 0.34+
**Why:** ASGI server for FastAPI. Production-grade, async, fast startup. Launched by Tauri as a sidecar process.

## Pydantic 2.x
**Why:** Data validation for FastAPI request/response models. Ensures type safety at the API boundary. Used in all router files for request body validation.
