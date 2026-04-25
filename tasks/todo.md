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
