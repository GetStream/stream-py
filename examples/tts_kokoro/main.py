#!/usr/bin/env python3
"""
Example: Text-to-Speech bot with Kokoro

This minimal example shows how to:
1. Spin up a Stream video call
2. Attach a Kokoro TTS bot that can speak into the call

Run it, join the call in your browser, and hear the bot greet you 🗣️

Usage::
    python main.py

The script looks for the following env vars (see `env.example`):
    STREAM_API_KEY / STREAM_API_SECRET

Kokoro runs fully offline – no extra API key required, but you **must** have
`espeak-ng` installed and available on the PATH for fallback phoneme
generation. On macOS: `brew install espeak-ng`.
"""

from __future__ import annotations

import asyncio
import logging
import os
from uuid import uuid4
import importlib, sys

from dotenv import load_dotenv

from examples.utils import create_user, open_browser
from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.rtc import audio_track
from getstream_kokoro import KokoroTTS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

os.environ["KOKORO_NO_AUTO_INSTALL"] = "1" # Disable auto-install of kokoro dependencies

# ---------------------------------------------------------------------------
# Ensure `pip` is present – uv-created virtual-envs omit it for speed and     
# Kokoro relies on `python -m pip` for optional installs (voices, extras).    
# Run this *before* we import Kokoro.                                         
# ---------------------------------------------------------------------------
try:
    importlib.import_module("pip")
except ModuleNotFoundError:  # pragma: no cover – only triggers in uv venvs
    import ensurepip, subprocess  # noqa: WPS433

    print("Boot-strapping pip (uv venv detected – pip missing)…", file=sys.stderr)
    ensurepip.bootstrap()
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

async def main() -> None:
    """Create a video call and let a Kokoro TTS bot greet participants."""

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    client: Stream = Stream.from_env()

    human_id = f"user-{uuid4()}"
    bot_id = f"tts-bot-{uuid4()}"

    create_user(client, human_id, "Human")
    create_user(client, bot_id, "TTS Bot")

    logging.info("Created users: %s (human) / %s (bot)", human_id, bot_id)

    token = client.create_token(human_id, expiration=3600)

    call_id = str(uuid4())
    call = client.video.call("default", call_id)
    call.get_or_create(data={"created_by_id": bot_id})

    logging.info("📞 Call ready: %s", call_id)

    open_browser(client.api_key, token, call_id)

    # Kokoro produces 24 kHz mono 16-bit PCM
    track = audio_track.AudioStreamTrack(framerate=24_000)

    # Build TTS pipeline (defaults to American English / af_heart voice)
    tts = KokoroTTS()
    tts.set_output_track(track)

    greeting = (
        "Hello there! I'm a Kokoro text-to-speech bot speaking inside this call. "
        "As this is a minimal example, I'll stop speaking now."
    )

    try:
        async with await rtc.join(call, bot_id) as connection:
            await connection.add_tracks(audio=track)
            logging.info("🤖 Bot joined call: %s", call_id)

            await asyncio.sleep(1)
            # Send greeting once the track is live
            await tts.send(greeting)
            logging.info("Sent greeting via TTS")

            logging.info("🎧 Bot is idle – press Ctrl+C to stop")
            await connection.wait()

    except (asyncio.CancelledError):
        logging.info("Stopping TTS bot…")
    finally:
        client.delete_users([human_id, bot_id])
        logging.info("Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main()) 