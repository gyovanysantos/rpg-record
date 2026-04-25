# RPG Session Recorder & Transcriber — Architecture

## Overview
A Python desktop application that records multi-channel RPG table sessions, transcribes each player's audio separately, merges the transcripts chronologically, and generates an AI-powered session summary.

## System Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                        Gradio UI (main.py)                      │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────┐ ┌─────────┐│
│  │  Device   │ │  Start/  │ │Transcribe │ │ Merge │ │Summarize││
│  │ Selector  │ │  Stop    │ │           │ │       │ │         ││
│  └──────────┘ └──────────┘ └───────────┘ └───────┘ └─────────┘│
└────────┬────────────┬────────────┬───────────┬──────────┬──────┘
         │            │            │           │          │
         ▼            ▼            ▼           ▼          ▼
    ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌───────┐ ┌─────────┐
    │config.py│ │recorder  │ │transcriber│ │merger  │ │summariz.│
    │         │ │    .py   │ │    .py    │ │  .py   │ │   .py   │
    └─────────┘ └────┬─────┘ └─────┬─────┘ └───┬───┘ └────┬────┘
                     │             │            │          │
                     ▼             │            │          │
               ┌──────────┐       │            │          │
               │processor │       │            │          │
               │   .py    │       │            │          │
               └──────────┘       │            │          │
                                  │            │          │
                     ┌────────────┘            │          │
                     ▼                         │          ▼
              ┌──────────────┐                 │   ┌──────────────┐
              │  Groq API    │                 │   │ Anthropic API│
              │  (Whisper)   │                 │   │  (Claude)    │
              └──────────────┘                 │   └──────────────┘
                                               │
         ┌─────────────────────────────────────┘
         ▼
    sessions/YYYY-MM-DD/
    ├── raw/           ← recorder.py writes here
    ├── processed/     ← processor.py writes here
    ├── transcripts/   ← transcriber.py + merger.py write here
    └── summary.md     ← summarizer.py writes here
```

## Module Responsibilities

### config.py
- Loads API keys from `.env` via `python-dotenv`
- Defines player-to-channel mapping (`PLAYERS` dict)
- Audio settings: `SAMPLE_RATE`, `AUDIO_DEVICE`, `NUM_CHANNELS`
- Silence stripping parameters
- `get_session_dir()` — creates dated session folders with auto-increment for same-day sessions
- `get_active_players()` — filters players by active channel count

### recorder.py
- `list_devices()` — enumerates available audio input devices via `sounddevice`
- `select_device()` — validates a device selection
- `Recorder` class — manages multi-channel audio recording via `sounddevice.InputStream`
  - Records to a thread-safe buffer
  - Computes per-channel RMS levels for live UI meters
  - On stop: splits multi-channel audio into per-channel `.wav` files

### processor.py
- `process_channel()` — strips silence from a single channel using `pydub.silence.split_on_silence()`
- `process_session()` — batch-processes all raw channels in a session
- Checks for `ffmpeg` availability at runtime

### transcriber.py
- `transcribe_channel()` — sends audio to Groq Whisper API, returns timestamped segments
- `transcribe_session()` — transcribes all processed channels, saves per-channel `.json`

### merger.py
- `merge_transcripts()` — loads all per-channel transcripts, sorts segments by timestamp, formats as `[MM:SS] Player Name: text`, saves `merged.txt`

### summarizer.py
- `summarize_session()` — sends merged transcript to Claude API with RPG scribe prompt, saves `summary.md`

### main.py
- Gradio Blocks UI with:
  - Device selection dropdown
  - Channel count selector (1 for laptop, 5 for Focusrite)

---

## Desktop App (`desktop-app/`)

A standalone PySide6 desktop application with a dark fantasy theme, built specifically for Shadow of the Demon Lord campaigns. Wraps the existing recording pipeline with a full RPG toolkit.

### Folder Structure
```
desktop-app/
├── main.py                     ← Entry point: loads theme, role picker, main window
├── build.spec                  ← PyInstaller config for .exe packaging
├── requirements.txt            ← PySide6, google-genai, markdown, pyinstaller
├── assets/
│   ├── styles/
│   │   └── dark_fantasy.qss    ← Full QSS theme (midnight blue + gold accents)
│   ├── fonts/                  ← (Future) custom gothic fonts
│   ├── images/                 ← (Future) icons, backgrounds
│   └── sounds/                 ← (Future) UI sound effects
├── app/
│   ├── core/
│   │   ├── recording_worker.py ← QTimer-based level polling + recording lifecycle
│   │   ├── pipeline_worker.py  ← QThread for process → transcribe → merge → summarize
│   │   └── narrator_worker.py  ← Gemini TTS narration engine (script + audio generation)
│   ├── models/
│   │   ├── campaign.py      ← Session scanning, campaign CRUD, SessionInfo/Campaign dataclasses
│   │   └── character.py     ← SotDL Character dataclass, save/load/list, derived stats
│   └── ui/
│       ├── role_picker.py      ← Startup dialog: DM vs Player role selection
│       ├── sidebar.py          ← Vertical nav panel, role-aware page switching
│       ├── main_window.py      ← QMainWindow: sidebar + QStackedWidget page stack
│       ├── pages/
│       │   ├── stubs.py        ← Placeholder pages for remaining sections
│       │   ├── recorder_page.py ← Full recording UI (device, channels, meters, pipeline)
│       │   ├── dashboard_page.py ← Campaign dashboard with stats + session history cards
│       │   ├── characters_page.py ← Full SotDL character sheet editor (list + tabs)
│       │   ├── dice_page.py       ← d20 + boons/banes roller with history
│       │   ├── initiative_page.py ← Fast/Slow turn tracker with combatant cards
│       │   ├── transcript_page.py ← Color-coded transcript viewer with search + export
│       │   └── narrator_page.py   ← Gemini TTS cinematic narration with audio player
│       └── widgets/
│           └── player_card.py  ← Player name + custom-painted LevelBar meter
└── data/
    ├── sotdl/
    │   └── game_data.json      ← SotDL reference: ancestries, paths, spell traditions
    ├── characters/             ← Saved character JSON files
    └── campaigns/              ← Campaign save data (campaign.json per campaign)
```

### Application Flow
```
main.py
  │
  ├── Load dark_fantasy.qss theme
  ├── Show RolePickerDialog (DM / Player)
  │
  └── MainWindow(role)
        ├── Sidebar (role-aware nav buttons)
        └── QStackedWidget
              ├── DashboardPage    ← Phase 3 ✅
              ├── RecorderPage     ← Phase 2 (DM only)
              ├── TranscriptPage   ← Phase 6
              ├── CharactersPage   ← Phase 4
              ├── InitiativePage   ← Phase 5
              ├── DicePage         ← Phase 5
              └── NarratorPage     ← Phase 7 (DM only)
```

### Role System
- **DM:** Full access — recording, transcription, campaigns, narration, all RPG tools
- **Player:** View-only for transcripts + full access to character sheets, dice, initiative

### Implementation Phases
| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Foundation (theme, nav, role picker, stubs) | ✅ Complete |
| 2 | Recording Engine (wrap existing modules) | ✅ Complete |
| 3 | Campaign Dashboard | ✅ Complete |
| 4 | Character Sheets (full SotDL) | ✅ Complete |
| 5 | RPG Tools (dice + initiative) | ✅ Complete |
| 6 | Transcript Viewer & Sharing | ✅ Complete |
| 7 | Gemini TTS Narration | ✅ Complete |
| 8 | Polish & PyInstaller Packaging | 🔲 Planned |
  - Player name fields
  - Live audio level indicators
  - Sequential action buttons: Start → Stop & Process → Transcribe → Merge → Summarize
  - Status log and output display

## Data Flow
```
Audio Input (mic/Focusrite)
    │
    ▼ [recorder.py]
raw/channel_0.wav ... channel_N.wav
    │
    ▼ [processor.py]
processed/channel_0.wav ... channel_N.wav  (silence stripped)
    │
    ▼ [transcriber.py]
transcripts/channel_0.json ... channel_N.json  (timestamped text)
    │
    ▼ [merger.py]
transcripts/merged.txt  (chronologically sorted, labeled)
    │
    ▼ [summarizer.py]
summary.md  (narrative summary, timeline, lore, characters, cliffhangers)
```

## Device Modes
| Mode    | Device              | Channels | Use Case           |
|---------|---------------------|----------|--------------------|
| Laptop  | Built-in mic        | 1        | Development/testing |
| Focusrite | Scarlett 6i6 USB  | 5        | Production sessions |
