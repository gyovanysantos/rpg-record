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
│   │   ├── narrator_worker.py  ← Gemini TTS narration engine (script + audio generation)
│   │   ├── settings_manager.py ← Centralized .env read/write for AI service settings
│   │   └── update_checker.py   ← Background version check against remote version.json
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
│       │   ├── narrator_page.py   ← Gemini TTS cinematic narration with audio player
│       │   └── settings_page.py   ← AI service configuration (API keys, models, test)
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
              ├── NarratorPage     ← Phase 7 (DM only)
              └── SettingsPage     ← Phase 8 (DM only)
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
| 8 | Settings Page (AI services) | ✅ Complete |
| 9 | Distribution Pipeline (.exe + updates) | ✅ Complete |
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

## Distribution Pipeline

### Version System
- Single source of truth: `desktop-app/app/__version__.py`
- Displayed in status bar: `v0.1.0`
- Read dynamically by `build.spec` to name the `.exe`

### Update Checker
- `update_checker.py` runs a background QThread on app start
- Fetches `version.json` from a public GitHub Gist (URL in `UPDATE_URL` constant)
- Compares remote vs local version; shows "Download" dialog if newer
- Silently fails on network errors (non-blocking)

### Release Workflow
```
Developer                           GitHub Actions
    │                                    │
    ├─ Bump __version__.py               │
    ├─ git commit + git tag v0.2.0       │
    ├─ git push --tags ──────────────────┤
    │                                    ├─ Checkout code
    │                                    ├─ Setup Python 3.12
    │                                    ├─ Install deps + ffmpeg
    │                                    ├─ PyInstaller build
    │                                    └─ Create GitHub Release + .exe asset
    │                                    │
    └── Friends download from Releases ◄─┘
```

### Local Build
- `scripts/build.ps1` — PowerShell script for local `.exe` builds

---

## Desktop App v2 (`desktop-app-v2/`) — Tauri + React + FastAPI

A complete rewrite of the desktop app using a modern web-based stack while keeping all existing Python backend modules intact.

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                     Tauri v2 (Rust Shell)                       │
│  - Native window management (1280x800, min 900x600)            │
│  - Launches FastAPI as sidecar process                         │
│  - File system access via Tauri APIs                           │
└────────────────────────┬────────────────────────────────────────┘
                         │ hosts
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              React 18 + TypeScript + Vite Frontend              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────┐   │
│  │ zustand  │ │ i18next  │ │ framer-  │ │ @tanstack/      │   │
│  │ (state)  │ │ (PT/EN)  │ │ motion   │ │ react-query     │   │
│  └──────────┘ └──────────┘ └──────────┘ └─────────────────┘   │
│  TailwindCSS dark fantasy theme (gold + midnight blue)         │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP REST + WebSocket
                         │ /api → localhost:8420
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Backend (localhost:8420)                    │
│  ┌────────────┐ ┌────────┐ ┌───────────┐ ┌──────────────────┐ │
│  │ characters │ │ spells │ │ game_data │ │   sessions       │ │
│  │   router   │ │ router │ │  router   │ │   router         │ │
│  └────────────┘ └────────┘ └───────────┘ └──────────────────┘ │
│  ┌────────────┐                                                │
│  │  settings  │  (Phase 3: recording, pipeline, narrator)      │
│  │   router   │                                                │
│  └────────────┘                                                │
│  Imports existing Python modules: recorder, processor,         │
│  transcriber, merger, summarizer, config                       │
└─────────────────────────────────────────────────────────────────┘
```

### Folder Structure
```
desktop-app-v2/
├── package.json                ← React + Tauri deps
├── vite.config.ts              ← Dev proxy /api→8420, /ws→ws://8420
├── tailwind.config.js          ← Dark fantasy theme + custom animations
├── index.html                  ← Entry point (lang="pt-BR")
├── src/
│   ├── main.tsx                ← React root: QueryClient, BrowserRouter, i18n
│   ├── App.tsx                 ← RolePicker gate → AppLayout with Routes
│   ├── i18n.ts                 ← react-i18next config (PT-BR default)
│   ├── index.css               ← Tailwind + custom component classes
│   ├── stores/
│   │   └── appStore.ts         ← zustand: role, sidebar state
│   ├── locales/
│   │   ├── pt-BR.json          ← Portuguese translation (~200 keys)
│   │   └── en.json             ← English translation
│   ├── components/layout/
│   │   ├── RolePicker.tsx      ← DM/Player selection screen
│   │   ├── Sidebar.tsx         ← Collapsible nav, role-aware filtering
│   │   └── AppLayout.tsx       ← Sidebar + animated page container
│   ├── components/
│   │   ├── cards/
│   │   │   ├── SpellCard.tsx       ← Flippable spell card (front/back, cast tracker)
│   │   │   └── SpellDeck.tsx       ← Filterable spell grid (search, tradition, rank)
│   │   ├── modals/
│   │   │   └── SpellPickerModal.tsx ← Modal to browse & pick spells from database
│   │   └── layout/
│   │       ├── RolePicker.tsx      ← DM/Player selection screen
│   │       ├── Sidebar.tsx         ← Collapsible nav, role-aware filtering
│   │       └── AppLayout.tsx       ← Sidebar + animated page container
│   ├── hooks/
│   │   ├── useCharacters.ts        ← CRUD hooks for characters (react-query)
│   │   ├── useSpells.ts            ← Spell & tradition hooks (react-query)
│   │   └── useGameData.ts          ← Ancestry, path, tradition hooks
│   └── pages/
│       ├── DashboardPage.tsx       ← Stats + recent sessions
│       ├── CharactersPage.tsx      ← Character list with create/delete
│       ├── CharacterSheetPage.tsx  ← Full tabbed character editor (see below)
│       ├── SpellsPage.tsx          ← Spell database browser (SpellDeck)
│       ├── TalentsPage.tsx         ← Talent cards (stub)
│       ├── DicePage.tsx            ← d20 + boons/banes roller (functional)
│       ├── InitiativePage.tsx      ← Fast/slow turn tracker (stub)
│       ├── RecorderPage.tsx        ← Audio recording (stub, DM only)
│       ├── TranscriptsPage.tsx     ← Transcript viewer (stub, DM only)
│       ├── NarratorPage.tsx        ← TTS narration (stub, DM only)
│       └── SettingsPage.tsx        ← Language + API keys (functional)
├── src-tauri/
│   ├── Cargo.toml              ← tauri 2 + shell plugin
│   ├── tauri.conf.json         ← Window config, dev server 1420
│   └── src/
│       ├── lib.rs              ← Tauri builder with shell plugin
│       └── main.rs             ← Windows entry point
└── backend/
    ├── main.py                 ← FastAPI app, CORS, router imports
    ├── requirements.txt        ← fastapi, uvicorn, pydantic, dotenv
    └── routers/
        ├── characters.py       ← CRUD: GET/POST/PUT/DELETE /api/characters
        ├── spells.py           ← Read-only: GET /api/spells, /api/spells/traditions
        ├── game_data.py        ← Read-only: ancestries, paths, traditions
        ├── sessions.py         ← List sessions, read transcripts/summaries
        └── settings.py         ← .env API key management (masked display)
```

### Communication Flow
```
React Component
  │
  ├─ useQuery / useMutation (@tanstack/react-query)
  │     │
  │     ▼
  │   fetch('/api/characters')  ← Vite dev proxy in dev mode
  │     │
  │     ▼
  │   FastAPI Router (localhost:8420)
  │     │
  │     ▼
  │   Existing Python module (character.py, etc.)
  │     │
  │     ▼
  │   JSON file on disk (data/characters/*.json)
  │
  └─ zustand store (local UI state: role, sidebar)
```

### i18n Strategy
- **UI strings**: Translated via react-i18next (`t('sidebar.spells')`)
- **Game data**: Stays in Portuguese (from the SotDL book in PT-BR)
- **Default language**: PT-BR, switchable to EN in Settings
- **Persistence**: Stored in `localStorage`

### Color Palette
| Token    | Hex       | Usage                    |
|----------|-----------|--------------------------|
| bg       | `#1a1a2e` | Page background          |
| surface  | `#16213e` | Cards, panels            |
| card     | `#0f3460` | Elevated cards           |
| accent   | `#c4a35a` | Gold highlights, buttons |
| text     | `#e0d6c8` | Primary text             |
| muted    | `#8a7e6b` | Secondary text           |
| danger   | `#8b0000` | Delete, errors           |
| success  | `#2e5e3e` | Confirm, online status   |
| border   | `#2a2a4a` | Dividers, outlines       |
- Installs deps, runs PyInstaller, reports output path and size

### CharacterSheetPage — Tabbed Architecture
The character sheet is the most complex page in the app, implemented with 5 tabs:

```
CharacterSheetPage.tsx (~650 lines)
  │
  ├─ Header: [← Voltar] [Name] [Level · Ancestry] [⚔️ Modo Combate] [🔒 Lock/Unlock]
  │
  ├─ Combat Mode Banner (visible when combat active)
  │    └─ Red pulsing banner: "⚔️ COMBATE ATIVO" with restore message
  │
  ├─ Combat End Confirmation Dialog (modal overlay)
  │    └─ "Encerrar Combate?" → "Continuar Combate" / "Encerrar e Restaurar"
  │
  ├─ Tab Bar: Stats | Magias | Talentos | Equipamento | Anotações
  │                    (badges show count when items exist)
  │
  ├─ Stats Tab
  │    ├─ Identity: Name, Level, Ancestry, Size, Novice/Expert/Master paths
  │    ├─ Attributes: Strength, Agility, Intellect, Will (with modifier calc)
  │    ├─ Health: HP bar, damage, healing rate, bonus
  │    ├─ Combat: Defense, Speed, Perception (icon cards + bonus fields)
  │    ├─ Secondary: Power, Corruption, Insanity, Fortune (checkbox), Gold
  │    └─ Languages & Professions
  │
  ├─ Spells Tab (SpellsTab component)
  │    ├─ SpellCard grid (interactive: cast/track castings per spell)
  │    ├─ "Adicionar Magia" → opens SpellPickerModal
  │    └─ Trash button per spell to remove from deck
  │
  ├─ Talents Tab (TalentsTab component)
  │    ├─ Inline CRUD cards: name, level (spinner), description
  │    ├─ "Adicionar Talento" button → adds empty card
  │    └─ Trash button per talent to remove
  │
  ├─ Equipment Tab (EquipmentTab component)
  │    ├─ Inline CRUD cards: name, category, equipped (checkbox), description
  │    ├─ "Adicionar Item" button → adds empty card
  │    └─ Trash button per item to remove
  │
  └─ Notes Tab
       └─ Full-width textarea for freeform notes (+ combat logs appended here)

Auto-save: All changes debounced (600ms) → PUT /api/characters/{name}
Lock/Unlock: Fields disabled by default; click 🔒 to enable editing

### Combat Mode
A sandbox feature that snapshots the character before combat and fully restores them afterward.

**Flow:**
1. Click "Modo Combate" → deep clone of character saved as snapshot → fields unlocked
2. During combat: take damage, cast spells, use fortune, spend gold freely
3. Click "Encerrar Combate" → confirmation dialog appears
4. On confirm: diff computed (damage, spells cast, fortune, gold, corruption, insanity)
5. Combat log saved as markdown in the character's Notes field
6. Character fully restored to pre-combat snapshot (notes updated with log)

**State variables:**
- `combatMode: boolean` — whether combat is active
- `combatSnapshot: CharacterFull | null` — deep clone from before combat
- `combatStartTime: Date | null` — for duration tracking
- `showCombatConfirm: boolean` — end combat confirmation dialog

**UI changes during combat:**
- Red pulsing banner at top with ⚔️ icon
- Lock button disabled (always unlocked during combat)
- "Modo Combate" button changes to red "Encerrar Combate"
- Outer container gets danger ring border
- Back button warns before navigating away (discards combat)
```

Key sub-components used:
- `SpellCard` (`components/cards/SpellCard.tsx`): Flippable card with front (name, tradition, rank badge) and back (description). Interactive mode shows casting tracker (click to cast, shows remaining).
- `SpellPickerModal` (`components/modals/SpellPickerModal.tsx`): Full-screen modal with SpellDeck (search, filter by tradition/rank), multi-select, confirm to add to character.
- `SpellDeck` (`components/cards/SpellDeck.tsx`): Filterable grid of SpellCards with search bar, tradition dropdown, and rank buttons.
