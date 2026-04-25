"""
Narrator Worker — Gemini TTS cinematic narration engine.

Two-step pipeline:
1. Transform the session summary into a dramatic narration script
   using Gemini's text model (with RPG narrator system prompt).
2. Convert the script to audio via Gemini TTS model with
   a dark fantasy narrator voice.

Runs on a QThread to keep the UI responsive.
Emits progress signals for each step.
"""

import wave
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QThread

from google import genai
from google.genai import types


# ── Voice Registry ──────────────────────────────────────────────
# Voices suited to dark fantasy narration. Each has a character.
VOICES = {
    "Charon":    "Informative — deep, authoritative narrator",
    "Fenrir":    "Excitable — intense, dramatic storyteller",
    "Orus":      "Firm — commanding, resolute voice",
    "Kore":      "Firm — steady, mythic tone",
    "Enceladus": "Breathy — whispered, eerie atmosphere",
    "Achird":    "Friendly — warm, tavern storyteller",
    "Gacrux":    "Mature — wise elder, gravitas",
    "Schedar":   "Even — calm, measured chronicler",
    "Rasalgethi": "Informative — scholarly, lore-keeper",
    "Sulafat":   "Warm — gentle, campfire narrator",
}

DEFAULT_VOICE = "Charon"

# ── Narration Styles ────────────────────────────────────────────
NARRATION_STYLES = {
    "Dark & Ominous": {
        "scene": (
            "A dimly lit stone chamber deep beneath a crumbling keep. "
            "A single candle gutters on a scarred oak table, casting "
            "long shadows across ancient tomes and scattered bones. "
            "The narrator sits hunched over a leather-bound chronicle, "
            "ink-stained fingers tracing the events of the last session."
        ),
        "director": (
            "Style: Dark, foreboding, and atmospheric. "
            "The narrator speaks as if recounting horrors witnessed firsthand. "
            "Occasional pauses for dramatic weight. "
            "A sense of dread permeates every sentence.\n"
            "Pacing: Measured and deliberate, slowing at moments of horror "
            "or revelation, quickening during action sequences.\n"
            "Accent: Deep, resonant, theatrical English."
        ),
        "tags": "[ominously]",
    },
    "Epic & Heroic": {
        "scene": (
            "A grand hall lit by roaring braziers. Banners of fallen kingdoms "
            "hang from the vaulted ceiling. The narrator stands before a "
            "gathered crowd, voice booming across the chamber as they recount "
            "the deeds of the adventurers."
        ),
        "director": (
            "Style: Grand, sweeping, and triumphant. "
            "The narrator speaks like a bard celebrating legendary deeds. "
            "Emphasis on courage, sacrifice, and glory.\n"
            "Pacing: Dynamic — building from quiet setup to thunderous climax. "
            "Elongate key words for emphasis.\n"
            "Accent: Rich, theatrical, commanding."
        ),
        "tags": "[dramatically]",
    },
    "Mysterious & Arcane": {
        "scene": (
            "A frost-bitten observatory atop a wizard's tower. Stars wheel "
            "overhead through a shattered dome. The narrator peers into a "
            "scrying pool, whispering the events they see rippling across "
            "its dark surface."
        ),
        "director": (
            "Style: Enigmatic, hushed, and wonder-filled. "
            "The narrator speaks as if revealing secrets that should remain hidden. "
            "A sense of cosmic mystery underlies every word.\n"
            "Pacing: Slow and deliberate, with meaningful pauses. "
            "Whispered passages for arcane revelations.\n"
            "Accent: Ethereal, slightly otherworldly."
        ),
        "tags": "[mysteriously]",
    },
    "Grim Chronicle": {
        "scene": (
            "A rain-soaked battlefield at dusk. Crows circle overhead. "
            "The narrator sits on an overturned wagon, writing by the "
            "fading light, recording what happened so it won't be forgotten."
        ),
        "director": (
            "Style: Somber, unflinching, matter-of-fact. "
            "The narrator reports events with weary pragmatism. "
            "No glory — just survival and consequence.\n"
            "Pacing: Steady and relentless, like a march. "
            "Brief pauses at moments of loss.\n"
            "Accent: Gruff, world-weary, honest."
        ),
        "tags": "[seriously]",
    },
}

DEFAULT_STYLE = "Dark & Ominous"

# ── System prompt for script generation ─────────────────────────
_SCRIPT_SYSTEM_PROMPT = """\
You are a master narrator for a dark fantasy tabletop RPG called \
Shadow of the Demon Lord. You transform dry session summaries into \
dramatic, evocative narration scripts meant to be read aloud.

RULES:
- Write in second/third person narrative voice ("The adventurers...", \
"Your party...")
- Include atmospheric descriptions: sounds, smells, weather, lighting
- Use dramatic pauses indicated by ellipsis (...)
- Add audio tag hints in square brackets for the TTS: [whispers], \
[dramatically], [ominously], [excitedly], [shouting], [sighs], [pause]
- Keep it under 800 words — this is a recap, not a novel
- Start with a compelling hook line
- End with a cliffhanger or dramatic closing
- Reference character names from the summary
- Maintain the dark, gritty tone of Shadow of the Demon Lord
- Do NOT include stage directions, speaker labels, or meta-commentary
- Output ONLY the narration script text, nothing else
"""


class NarratorWorker(QObject):
    """
    Background worker that generates cinematic narration audio.

    Signals:
        progress(str)  — status message for each step
        script_ready(str) — the generated narration script text
        audio_ready(str)  — path to the saved WAV file
        error(str)     — error message if something fails
        finished()     — work complete
    """

    progress = Signal(str)
    script_ready = Signal(str)
    audio_ready = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(self, api_key: str, summary_text: str, output_dir: Path,
                 voice: str = DEFAULT_VOICE, style: str = DEFAULT_STYLE,
                 script_model: str = "gemini-2.5-flash",
                 parent=None):
        super().__init__(parent)
        self._api_key = api_key
        self._summary = summary_text
        self._output_dir = Path(output_dir)
        self._voice = voice
        self._style = style
        self._script_model = script_model
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        """Execute the two-step narration pipeline."""
        try:
            client = genai.Client(api_key=self._api_key)

            # ── Step 1: Generate dramatic narration script ──────
            if self._cancelled:
                return

            self.progress.emit("✍️  Crafting dramatic narration script...")
            script = self._generate_script(client)
            if self._cancelled:
                return

            self.script_ready.emit(script)
            self.progress.emit("📜  Script ready! Generating audio...")

            # ── Step 2: Convert script to audio via TTS ─────────
            audio_path = self._generate_audio(client, script)
            if self._cancelled:
                return

            self.audio_ready.emit(str(audio_path))
            self.progress.emit("✅  Narration complete!")

        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def _generate_script(self, client: genai.Client) -> str:
        """Use Gemini text model to transform summary → dramatic script."""
        style_info = NARRATION_STYLES.get(self._style, NARRATION_STYLES[DEFAULT_STYLE])

        prompt = (
            f"Transform this RPG session summary into a dramatic narration "
            f"script. The tone should be: {self._style}.\n\n"
            f"SUMMARY:\n{self._summary}"
        )

        response = client.models.generate_content(
            model=self._script_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SCRIPT_SYSTEM_PROMPT,
                temperature=0.9,
                max_output_tokens=2048,
            ),
        )
        return response.text.strip()

    def _generate_audio(self, client: genai.Client, script: str) -> Path:
        """Use Gemini TTS model to convert script → WAV audio."""
        style_info = NARRATION_STYLES.get(self._style, NARRATION_STYLES[DEFAULT_STYLE])

        # Build the full TTS prompt with audio profile and scene
        tts_prompt = (
            f"# AUDIO PROFILE: The Chronicler\n"
            f"## Dark Fantasy Session Narrator\n\n"
            f"## THE SCENE\n{style_info['scene']}\n\n"
            f"### DIRECTOR'S NOTES\n{style_info['director']}\n\n"
            f"### TRANSCRIPT\n"
            f"{style_info['tags']} {script}"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=tts_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self._voice,
                        )
                    )
                ),
            ),
        )

        # Extract PCM data and save as WAV
        data = response.candidates[0].content.parts[0].inline_data.data
        self._output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self._output_dir / "narration.wav"

        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)       # 16-bit
            wf.setframerate(24000)   # Gemini TTS default rate
            wf.writeframes(data)

        return output_path
