"""
main.py — Gradio UI for RPG Session Recorder & Transcriber.

Provides a web-based interface with:
- Device selection dropdown
- Channel count selector (1 for laptop, 5 for Focusrite)
- Player name fields
- Live audio level indicators
- Sequential action buttons: Start → Stop & Process → Transcribe → Merge → Summarize
- Status log and output display
"""

import time
import threading
import gradio as gr
from pathlib import Path

from config import (
    PLAYERS, SAMPLE_RATE, NUM_CHANNELS, AUDIO_DEVICE,
    get_session_dir, get_active_players,
)
from recorder import list_devices, Recorder
from processor import process_session
from transcriber import transcribe_session
from merger import merge_transcripts
from summarizer import summarize_session

# --- Global State ---
# These hold the current session's state across UI interactions
current_recorder: Recorder | None = None
current_session_dir: Path | None = None


def get_device_choices() -> list[str]:
    """Get formatted device list for the dropdown."""
    devices = list_devices()
    if not devices:
        return ["No input devices found"]
    return [f"[{d['index']}] {d['name']} ({d['max_channels']} ch)" for d in devices]


def parse_device_index(device_str: str) -> int | None:
    """Extract device index from dropdown string like '[0] Microphone (2 ch)'."""
    if not device_str or device_str.startswith("No input"):
        return None
    try:
        return int(device_str.split("]")[0].strip("["))
    except (ValueError, IndexError):
        return None


def start_session(device_str: str, num_channels: int, *player_names) -> str:
    """
    Start a recording session.

    Creates a new session directory, initializes the recorder,
    and begins capturing audio from the selected device.
    """
    global current_recorder, current_session_dir

    if current_recorder and current_recorder.is_recording:
        return "⚠️ Already recording! Stop the current session first."

    device_index = parse_device_index(device_str)
    num_channels = int(num_channels)

    # Create session directory
    current_session_dir = get_session_dir()

    # Initialize and start recorder
    current_recorder = Recorder(
        device_index=device_index,
        num_channels=num_channels,
        sample_rate=SAMPLE_RATE,
    )

    try:
        current_recorder.start(current_session_dir)
    except Exception as e:
        current_session_dir = None
        current_recorder = None
        return f"❌ Failed to start recording: {e}"

    return (
        f"🔴 Recording started!\n"
        f"  Device: {device_str}\n"
        f"  Channels: {num_channels}\n"
        f"  Session: {current_session_dir.name}\n"
        f"  Sample rate: {SAMPLE_RATE} Hz"
    )


def stop_and_process(*player_names) -> str:
    """
    Stop recording and process (strip silence from) all channels.
    """
    global current_recorder

    if not current_recorder or not current_recorder.is_recording:
        return "⚠️ Not currently recording."

    # Stop recording
    log = "⏹️ Stopping recording...\n"
    try:
        saved_files = current_recorder.stop()
    except Exception as e:
        return f"❌ Error stopping recording: {e}"

    log += f"  Saved {len(saved_files)} raw file(s)\n\n"

    # Process (strip silence)
    log += "🔧 Processing audio (stripping silence)...\n"
    try:
        results = process_session(current_session_dir)
    except RuntimeError as e:
        return log + f"❌ Processing failed: {e}"

    for r in results:
        log += (
            f"  {r['channel']}: "
            f"{r['original_duration_ms']/1000:.1f}s → "
            f"{r['processed_duration_ms']/1000:.1f}s "
            f"({r['reduction_pct']}% reduction)\n"
        )

    log += "\n✅ Processing complete! Ready to transcribe."
    return log


def transcribe(num_channels: int, *player_names) -> str:
    """
    Transcribe all processed audio files using Groq Whisper.
    """
    if not current_session_dir:
        return "⚠️ No active session. Record and process first."

    num_channels = int(num_channels)

    # Build players map from UI inputs
    players = {}
    for i in range(num_channels):
        if i < len(player_names) and player_names[i]:
            players[f"channel_{i}"] = player_names[i]
        else:
            players[f"channel_{i}"] = PLAYERS.get(f"channel_{i}", f"Channel {i}")

    log = "🎤 Transcribing with Groq Whisper...\n"
    try:
        results = transcribe_session(current_session_dir, players)
    except ValueError as e:
        return log + f"❌ {e}"
    except Exception as e:
        return log + f"❌ Transcription failed: {e}"

    for r in results:
        seg_count = len(r["segments"])
        text_preview = " ".join(s["text"] for s in r["segments"])[:80]
        log += f"  {r['player']}: {seg_count} segments — \"{text_preview}...\"\n"

    log += f"\n✅ Transcription complete! {len(results)} channel(s) transcribed."
    return log


def merge(num_channels: int, *player_names) -> tuple[str, str]:
    """
    Merge all transcripts into one chronological file.

    Returns:
        Tuple of (status log, merged transcript text).
    """
    if not current_session_dir:
        return "⚠️ No active session.", ""

    num_channels = int(num_channels)

    players = {}
    for i in range(num_channels):
        if i < len(player_names) and player_names[i]:
            players[f"channel_{i}"] = player_names[i]
        else:
            players[f"channel_{i}"] = PLAYERS.get(f"channel_{i}", f"Channel {i}")

    log = "📋 Merging transcripts...\n"
    try:
        merged_path = merge_transcripts(current_session_dir, players)
    except Exception as e:
        return log + f"❌ Merge failed: {e}", ""

    if merged_path.exists():
        content = merged_path.read_text(encoding="utf-8")
        line_count = len(content.splitlines())
        log += f"  Merged into {line_count} lines\n"
        log += "✅ Merge complete! Ready to summarize."
        return log, content
    else:
        return log + "❌ Merged file not created.", ""


def summarize() -> tuple[str, str]:
    """
    Send merged transcript to Claude for summarization.

    Returns:
        Tuple of (status log, summary text).
    """
    if not current_session_dir:
        return "⚠️ No active session.", ""

    log = "🤖 Sending to Claude for summarization...\n"
    try:
        summary_path = summarize_session(current_session_dir)
    except (ValueError, FileNotFoundError) as e:
        return log + f"❌ {e}", ""
    except Exception as e:
        return log + f"❌ Summarization failed: {e}", ""

    if summary_path.exists():
        content = summary_path.read_text(encoding="utf-8")
        log += f"  Summary: {len(content)} characters\n"
        log += f"  Saved to: {summary_path}\n"
        log += "✅ Summarization complete!"
        return log, content
    else:
        return log + "❌ Summary file not created.", ""


def poll_levels() -> str:
    """Get current audio levels as a text-based meter display."""
    if not current_recorder or not current_recorder.is_recording:
        return "Not recording."

    levels = current_recorder.get_levels()
    bars = []
    for i, level in enumerate(levels):
        bar_length = int(level * 50)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        player = PLAYERS.get(f"channel_{i}", f"Ch {i}")
        bars.append(f"{player:15s} |{bar}| {level:.4f}")

    return "\n".join(bars)


# --- Build the Gradio UI ---
def create_ui():
    """
    Build and return the Gradio Blocks interface.

    Layout:
    - Top row: Device selector + channel count
    - Player name fields (dynamic based on channel count)
    - Live audio level display
    - Action buttons in pipeline order
    - Status log
    - Output tabs for transcript and summary
    """

    with gr.Blocks(title="RPG Session Recorder") as app:
        gr.Markdown("# 🎲 RPG Session Recorder & Transcriber")
        gr.Markdown(
            "Record your RPG session, transcribe each player, "
            "and generate an AI-powered summary."
        )

        # --- Device & Channel Settings ---
        with gr.Row():
            device_dropdown = gr.Dropdown(
                choices=get_device_choices(),
                label="Audio Input Device",
                value=get_device_choices()[0] if get_device_choices() else None,
                scale=3,
            )
            channel_count = gr.Number(
                label="Number of Channels",
                value=NUM_CHANNELS,
                minimum=1,
                maximum=8,
                step=1,
                scale=1,
            )

        # --- Player Names ---
        gr.Markdown("### Player Names")
        gr.Markdown("*Assign a name to each channel. Only active channels are used.*")

        player_inputs = []
        with gr.Row():
            for i in range(5):
                default_name = PLAYERS.get(f"channel_{i}", f"Channel {i}")
                inp = gr.Textbox(
                    label=f"Channel {i}",
                    value=default_name,
                    visible=(i < NUM_CHANNELS),
                )
                player_inputs.append(inp)

        # Update visibility when channel count changes
        def update_player_visibility(num_ch):
            num_ch = int(num_ch)
            return [gr.update(visible=(i < num_ch)) for i in range(5)]

        channel_count.change(
            fn=update_player_visibility,
            inputs=[channel_count],
            outputs=player_inputs,
        )

        # --- Audio Levels ---
        gr.Markdown("### Audio Levels")
        levels_display = gr.Textbox(
            label="Live Levels",
            value="Not recording.",
            lines=5,
            interactive=False,
        )

        # --- Action Buttons ---
        gr.Markdown("### Pipeline Controls")
        with gr.Row():
            btn_start = gr.Button("🔴 Start Session", variant="primary")
            btn_stop = gr.Button("⏹️ Stop & Process", variant="secondary")
            btn_transcribe = gr.Button("🎤 Transcribe", variant="secondary")
            btn_merge = gr.Button("📋 Merge", variant="secondary")
            btn_summarize = gr.Button("🤖 Summarize", variant="secondary")

        # --- Status Log ---
        status_log = gr.Textbox(
            label="Status",
            value="Ready. Select a device and click 'Start Session'.",
            lines=10,
            interactive=False,
        )

        # --- Output Tabs ---
        with gr.Tabs():
            with gr.Tab("Merged Transcript"):
                transcript_output = gr.Textbox(
                    label="Merged Transcript",
                    lines=20,
                    interactive=False,
                )
            with gr.Tab("Session Summary"):
                summary_output = gr.Markdown(label="Summary")

        # --- Wire up buttons ---
        btn_start.click(
            fn=start_session,
            inputs=[device_dropdown, channel_count] + player_inputs,
            outputs=[status_log],
        )

        btn_stop.click(
            fn=stop_and_process,
            inputs=player_inputs,
            outputs=[status_log],
        )

        btn_transcribe.click(
            fn=transcribe,
            inputs=[channel_count] + player_inputs,
            outputs=[status_log],
        )

        btn_merge.click(
            fn=merge,
            inputs=[channel_count] + player_inputs,
            outputs=[status_log, transcript_output],
        )

        btn_summarize.click(
            fn=summarize,
            inputs=[],
            outputs=[status_log, summary_output],
        )

        # --- Auto-refresh audio levels while recording ---
        # Uses Gradio's timer/polling to update levels display
        levels_timer = gr.Timer(value=0.5)
        levels_timer.tick(
            fn=poll_levels,
            inputs=[],
            outputs=[levels_display],
        )

    return app


# --- Entry point ---
if __name__ == "__main__":
    app = create_ui()
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(),
    )
