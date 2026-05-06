"""
RPG Record — FastAPI Backend
Serves as the bridge between the React frontend and the existing Python modules.
Runs on http://127.0.0.1:8420
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directories to sys.path so we can import existing modules
# (recorder, processor, transcriber, merger, summarizer, config)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # rpg-record/
DESKTOP_APP_DIR = ROOT_DIR / "desktop-app"
BACKEND_DIR = Path(__file__).resolve().parent  # desktop-app-v2/backend/

for p in [str(ROOT_DIR), str(DESKTOP_APP_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from routers import characters, spells, game_data, sessions, settings

app = FastAPI(
    title="RPG Record API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow the Vite dev server and Tauri webview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "https://tauri.localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(characters.router, prefix="/api/characters", tags=["Characters"])
app.include_router(spells.router, prefix="/api/spells", tags=["Spells"])
app.include_router(game_data.router, prefix="/api/game-data", tags=["Game Data"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
