#!/usr/bin/env python3
"""
Example: Real-time Call Transcription with Moonshine STT

Uses the local Moonshine model via the Moonshine plugin in this repo.

Steps:
1. Create two temporary Stream users (human + bot)
2. Spin up a new call and open it in your browser
3. The bot joins and pipes every audio frame to Moonshine STT
4. Final transcripts are printed with timestamps

Run:
    python main.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from dotenv import load_dotenv

from getstream.plugins.vad.silero.vad import Silero
from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.rtc.track_util import PcmData
from getstream.plugins.stt.moonshine import Moonshine
from examples.utils import create_user, open_browser


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


async def main() -> None:  # noqa: D401
    print("🌙  Stream + Moonshine Real-time Transcription Example")
    print("=" * 60)

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    client = Stream.from_env()

    call_id = str(uuid.uuid4())
    print(f"📞 Call ID: {call_id}") 

    user_id = f"user-{uuid.uuid4()}"
    create_user(client, user_id, "My User")
    logging.info("👤 Created user: %s", user_id)

    user_token = client.create_token(user_id, expiration=3600)

    bot_user_id = f"moonshine-bot-{uuid.uuid4()}"
    create_user(client, bot_user_id, "Moonshine Bot")
    logging.info("🤖 Created bot user: %s", bot_user_id)

    call = client.video.call("default", call_id)
    call.get_or_create(data={"created_by_id": bot_user_id})
    print(f"📞 Call created: {call_id}")

    open_browser(client.api_key, user_token, call_id)

    print("\n🤖 Starting transcription bot…")
    print("Speak in the browser and see transcripts below. Press Ctrl+C to stop.\n")

    stt = Moonshine()

    # Initialize Silero VAD for speech detection
    print("🔊 Initializing Silero VAD...")
    vad = Silero()
    print("✅ Audio processing pipeline ready: VAD → Moonshine STT")

    try:
        async with await rtc.join(call, bot_user_id) as connection:
            print(f"✅ Bot joined call: {call_id}")

            @connection.on("audio")
            async def _on_audio(pcm: PcmData, user):
                await vad.process_audio(pcm, user)

            @vad.on("audio")
            async def _on_speech_detected(pcm: PcmData, user):
                print(f"🎤 Speech detected from user: {user.name}, duration: {pcm.duration:.2f}s")
                await stt.process_audio(pcm, user)

            @stt.on("transcript")
            async def _on_transcript(text: str, user: any, metadata: dict):
                ts = time.strftime("%H:%M:%S")
                who = user if user else "unknown"
                print(f"[{ts}] {who}: {text}")

            @stt.on("error")
            async def _on_error(err):
                print(f"\n❌ STT Error: {err}")

            print("🎧 Listening for audio… (Press Ctrl+C to stop)")
            await connection.wait()

    except asyncio.CancelledError:
        print("\n⏹️  Stopping transcription bot…")
    except Exception as e:  # noqa: BLE001
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await stt.close()
        client.delete_users([user_id, bot_user_id])
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
