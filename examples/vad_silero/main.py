#!/usr/bin/env python3
"""
Example: Voice-Activity-Detection bot (Silero VAD)

The script joins a Stream video call with a bot that detects when anyone
speaks, using the Silero VAD plugin (`getstream.plugins.vad.silero`).
Each complete speech turn is logged with a timestamp and duration.

Run:
    python main.py

Environment: copy `examples/env.example` to `.env` and fill in
`STREAM_API_KEY`, `STREAM_API_SECRET` (and optionally `STREAM_BASE_URL`).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

from examples.utils import create_user, open_browser
from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.rtc.track_util import PcmData
from getstream.plugins.silero import SileroVAD

# ---------------------------------------------------------------------------
# Logging setup – INFO level so we see joins / leaves, etc.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)


async def main() -> None:
    """Create a call and start the Silero VAD bot."""

    # Load env from examples/.env
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    client = Stream.from_env()

    human_id = f"user-{uuid4()}"
    bot_id = f"vad-bot-{uuid4()}"

    create_user(client, human_id, "Human")
    create_user(client, bot_id, "VAD Bot")

    token = client.create_token(human_id, expiration=3600)

    call_id = str(uuid4())
    call = client.video.call("default", call_id)
    call.get_or_create(data={"created_by_id": bot_id})

    logging.info("📞 Call ready: %s", call_id)

    open_browser(client.api_key, token, call_id)

    vad = SileroVAD()

    print("\n🤖 VAD bot starting – speak in the call and watch the console.\n")

    speech_segments: list[dict[str, Any]] = []

    try:
        async with await rtc.join(call, bot_id) as connection:
            logging.info("🤖 Bot joined call: %s", call_id)

            # Forward audio frames to the VAD engine
            @connection.on("audio")
            async def _on_pcm(pcm: PcmData, user):
                await vad.process_audio(pcm, user)

            # Complete speech turns
            @vad.on("audio")  # type: ignore[arg-type]
            async def _on_turn(pcm: PcmData, user):
                duration = pcm.duration
                ts = time.strftime("%H:%M:%S")
                print(f"[{ts}] Speech from {user} — {duration:.2f}s")
                speech_segments.append({
                    "timestamp": ts,
                    "duration": duration,
                    "user": user,
                })

            # Optional: in-progress indicator
            @vad.on("partial")  # type: ignore[arg-type]
            async def _on_partial(_: PcmData, user):
                print(f"    {user} … speaking", end="\r")

            print("🎧 Listening… press Ctrl-C to stop")
            await connection.wait()

    except (asyncio.CancelledError, KeyboardInterrupt):
        print("\n⏹️  Stopping VAD bot…")
    finally:
        await vad.close()

        print(f"Detected {len(speech_segments)} speech segments")
        total_duration = sum(segment["duration"] for segment in speech_segments)
        print(f"Total speech duration: {total_duration:.2f} seconds")

        client.delete_users([human_id, bot_id])
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main()) 