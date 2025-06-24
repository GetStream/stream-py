#!/usr/bin/env python3
"""
Example: Text-to-Speech bot with Cartesia

This minimal example shows how to:
1. Spin up a Stream video call
2. Attach a Cartesia TTS bot that can speak into the call

Run it, join the call in your browser, and hear the bot greet you 🗣️

Usage::
    python main.py

The script looks for the following env vars (see `env.example`):
    STREAM_API_KEY / STREAM_API_SECRET
    CARTESIA_API_KEY
"""

from __future__ import annotations

import asyncio
import logging
import os
from uuid import uuid4

from dotenv import load_dotenv

from examples.utils import create_user, open_browser
from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.rtc import audio_track
from getstream_cartesia import CartesiaTTS


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

async def main() -> None:
    """Create a video call and let a TTS bot greet participants."""

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    client = Stream.from_env()

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

    track = audio_track.AudioStreamTrack(framerate=16000)
    tts = CartesiaTTS()  # API key picked from CARTESIA_API_KEY
    tts.set_output_track(track)

    greeting = "Hello there! I'm a Cartesia TTS bot speaking inside this call. As this is a minimal example, I'll stop speaking now."

    try:
        async with await rtc.join(call, bot_id) as connection:
            await connection.add_tracks(audio=track)
            logging.info("🤖 Bot joined call: %s", call_id)

            await connection.publisher_pc.wait_for_connected()

            someone_joined = asyncio.Event()

            @connection.participants_state.on("participant_joined")
            def _on_participant_joined(p):
                if p.user_id != bot_id:  # ignore the bot itself
                    someone_joined.set()

            # There may already be people in the call, so check once immediately
            if connection.participants_state.get_user_from_track_id(track.id):
                someone_joined.set()

            await someone_joined.wait()  # blocks here until a listener is present

            # Now it's safe to speak – nothing will be lost
            await tts.send(greeting)
            logging.info("Sent greeting via TTS")

            logging.info("🎧 Bot is idle - press Ctrl+C to stop")
            await connection.wait()

    except (asyncio.CancelledError):
        logging.info("Stopping TTS bot…")
    finally:
        client.delete_users([human_id, bot_id])
        logging.info("Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main()) 