# RPG Session Recorder — Task Tracker

## Phase 1: Project Setup
- [x] Create requirements.txt
- [x] Create .env.example and .env
- [x] Create .gitignore
- [x] Create config.py
- [x] Create ARCHITECTURE.md
- [x] Create TECH-STACK.md
- [x] Create LEARNING.md, LESSONS.md
- [x] ~~Create and activate venv~~ — Using system Python (venv pip broken)
- [x] Install dependencies via pip (keyring bypass required)
- [x] Install ffmpeg via winget
- [x] Verify: `python -c "import config"` runs clean

## Phase 2: recorder.py
- [x] Create recorder.py with list_devices(), select_device(), Recorder class
- [x] Test: record 5s from laptop mic, verify .wav is created ✓ (428KB, 5.0s)

## Phase 3: processor.py
- [x] Create processor.py with process_channel(), process_session(), ffmpeg check
- [x] Test: process a recording, verify output is shorter ✓ (19.4% reduction)
- [x] Bug fix: Add Path conversion for string inputs

## Phase 4: transcriber.py
- [x] Create transcriber.py with transcribe_channel(), transcribe_session()
- [x] Bug fix: Add Path conversion for string inputs
- [x] Test: transcribe a recording ✓ (Groq Whisper → "Excuse me." 1 segment)

## Phase 5: merger.py
- [x] Create merger.py with merge_transcripts()
- [x] Bug fix: Add Path conversion for string inputs
- [x] Test: merge transcripts ✓ ("[00:00] Dungeon Master: Excuse me.")

## Phase 6: summarizer.py
- [x] Create summarizer.py with summarize_session()
- [x] Bug fix: Add Path conversion for string inputs
- [x] Test: summarize merged transcript ✓ (Claude responded, 737 chars)

## Phase 7: main.py (Gradio UI)
- [x] Create main.py with Gradio Blocks UI
- [x] Fix: Move theme param to launch() for Gradio 6.0 compat
- [x] Test: UI launches at http://127.0.0.1:7860 ✓
- [x] Test: full end-to-end pipeline ✓ (Record → Process → Transcribe → Merge → Summarize)

## Phase 8: Desktop App v2 — Card UX Overhaul (feature/card-ux-overhaul)
- [x] Test Tauri desktop build — fixed config issues, built successfully
- [x] Add Invocations tab to CharacterSheetPage (card-style creature stat blocks)
  - [x] Create InvocationCard.tsx (expandable card with difficulty color, stats grid)
  - [x] Create InvocationEditorModal.tsx (template search from creatures.json + full form)
  - [x] Create useCreatures.ts hook (fetch creature templates from backend)
  - [x] Add creatures endpoint to game_data.py router
  - [x] Add i18n translations (EN + PT-BR, 28 keys)
  - [x] Integrate into CharacterSheetPage as 6th tab (between Talents and Equipment)
  - [x] Vite build verified — zero errors (2030 modules)
- [x] Update ARCHITECTURE.md with Invocations components
- [ ] Add v1→v2 data migration safety constraint

## Review
- All modules tested and working as of April 25, 2026
- Full pipeline verified: Record → Process (64.9% silence stripped) → Transcribe (Groq) → Merge → Summarize (Claude)
- Remaining: Multi-channel test with Focusrite Scarlett 6i6 (real RPG session)

---

## Desktop App — Phase 1: Foundation ✅
- [x] Create `desktop-app/` folder structure (assets, app, data, pages, widgets)
- [x] Install PySide6 6.11.0
- [x] Create `requirements.txt` (PySide6, google-genai, markdown, pyinstaller)
- [x] Create `dark_fantasy.qss` — full dark theme (#1a1a2e bg, #c4a35a gold accents)
- [x] Create `role_picker.py` — DM/Player startup dialog
- [x] Create `sidebar.py` — vertical nav with role-aware page visibility
- [x] Create `stubs.py` — placeholder pages for all 7 sections
- [x] Create `main_window.py` — QMainWindow with sidebar + QStackedWidget
- [x] Create `main.py` — entry point (loads QSS, role picker, main window)
- [x] Create `build.spec` — PyInstaller packaging config
- [x] Verify: app launches cleanly, role picker → main window works ✓
- [x] Update ARCHITECTURE.md and TECH-STACK.md

## Desktop App — Phase 2: Recording Engine ✅
- [x] Create `recording_worker.py` — QTimer-based level polling, elapsed time tracking
- [x] Create `pipeline_worker.py` — QThread for process → transcribe → merge → summarize
- [x] Create `player_card.py` — custom-painted LevelBar + player info widget
- [x] Create `recorder_page.py` — device dropdown, channel spinner, player cards, controls
- [x] Wire RecorderPage into MainWindow (replace stub import)
- [x] Fix sys.path: repo root added in main.py before any imports
- [x] Verify: app launches cleanly, Recorder page renders ✓

## Desktop App — Phase 3: Campaign Dashboard
- [ ] Session history list
- [ ] Campaign management (create, select)

## Desktop App — Phase 4: Character Sheets
- [ ] Full SotDL stat blocks (4 attributes, derived stats)
- [ ] Ancestry, Novice/Expert/Master paths
- [ ] Spells, corruption, insanity tracking

## Desktop App — Phase 5: RPG Tools
- [ ] Dice roller (d20 + boons/banes)
- [ ] Initiative tracker (fast/slow turn)

## Desktop App — Phase 6: Transcript Viewer
- [ ] Colored transcript display
- [ ] Export/import file-based sharing

## Desktop App — Phase 7: Gemini TTS Narrator
- [ ] Cinematic narration with multi-speaker voices

## Desktop App — Phase 8: Polish & Packaging
- [ ] PyInstaller .exe build
- [ ] Icon, splash screen, final polish

---

## Desktop App v2 — Tauri + React Migration

### Phase 0: Game Data Updates ✅
- [x] Add 11 Primal (Primitiva) spells to `spells.json` (34 traditions total)
- [x] Add "Primal" to `game_data.json` spell_traditions array

### Phase 1: Project Scaffold ✅
- [x] Create `desktop-app-v2/` with package.json, vite.config.ts, tailwind.config.js
- [x] Create Tauri config (Cargo.toml, tauri.conf.json, lib.rs, main.rs)
- [x] Create React entry (main.tsx, App.tsx, index.css, vite-env.d.ts)
- [x] Create i18n setup (i18n.ts, pt-BR.json, en.json)
- [x] Create zustand store (appStore.ts)
- [x] Create layout components (RolePicker, Sidebar, AppLayout)
- [x] Create all page stubs (Dashboard, Characters, Spells, Talents, Dice, Initiative, Recorder, Transcripts, Narrator, Settings)
- [x] Create FastAPI backend (main.py + 5 routers: characters, spells, game_data, sessions, settings)
- [x] Update ARCHITECTURE.md and TECH-STACK.md

### Phase 2: Setup & Verify (user action needed)
- [ ] `git checkout -b feature/card-ux-overhaul`
- [ ] `cd desktop-app-v2 && npm install`
- [ ] `cd backend && pip install -r requirements.txt`
- [ ] Verify frontend runs: `npm run dev`
- [ ] Verify backend runs: `uvicorn backend.main:app --port 8420`

### Phase 3: Core Functionality
- [ ] Recording, pipeline, and narrator routers (FastAPI)
- [ ] WebSocket for live audio levels

### Phase 4: Card-Based Spells ✅
- [x] SpellCard component (flip animation, rank badge, tradition color)
- [x] SpellDeck grid with filtering/search
- [x] SpellPickerModal for character sheet
- [x] React-query hooks for /api/spells

### Phase 5: Card-Based Talents
- [ ] TalentCard component
- [ ] TalentDeck grid
- [ ] TalentPickerModal for character sheet

### Phase 6: Character Sheet (full port) ✅
- [x] Character form with all SotDL fields (5 tabs: Stats, Spells, Talents, Equipment, Notes)
- [x] Spell/Talent card integration (SpellPickerModal + inline CRUD)
- [ ] Portrait upload
- [x] Combat Mode (snapshot/restore sandbox for encounters + combat log in Notes)

### Phase 7: Remaining Pages (full port)
- [ ] RecorderPage with live audio meters
- [ ] TranscriptsPage with search + export
- [ ] NarratorPage with voice selection + audio player
- [ ] DashboardPage with live data from API

### Phase 8: Distribution
- [ ] Tauri build (.exe)
- [ ] FastAPI sidecar packaging
- [ ] Installer / auto-update
