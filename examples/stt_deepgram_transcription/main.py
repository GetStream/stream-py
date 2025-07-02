#!/usr/bin/env python3
"""
Example: Real-time Call Transcription with Deepgram STT

This example demonstrates how to:
1. Join a Stream video call
2. Transcribe audio in real-time using Deepgram
3. Open a browser link for users to join the call

Usage:
    python main.py

Requirements:
    - Create a .env file with your Stream and Deepgram credentials (see env.example)
    - Install dependencies: pip install -e .
"""

import asyncio
import logging
import time
import uuid
from dotenv import load_dotenv

from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.rtc.track_util import PcmData
from getstream.plugins.deepgram import DeepgramSTT
from examples.utils import create_user, open_browser

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


async def main():
    """Main example function."""
    print("🎙️  Stream + Deepgram Real-time Transcription Example")
    print("=" * 55)

    # Load environment variables
    load_dotenv()

    # Initialize Stream client from ENV
    client = Stream.from_env()

    # Create a unique call ID for this session
    call_id = str(uuid.uuid4())
    print(f"📞 Call ID: {call_id}")

    user_id = f"user-{uuid.uuid4()}"
    create_user(client, user_id, "My User")
    logging.info("👤 Created user: %s", user_id)

    user_token = client.create_token(user_id, expiration=3600)
    logging.info("🔑 Created token for user: %s", user_id)

    bot_user_id = f"transcription-bot-{uuid.uuid4()}"
    create_user(client, bot_user_id, "Transcription Bot")
    logging.info("🤖 Created bot user: %s", bot_user_id)

    # Create the call
    call = client.video.call("default", call_id)
    call.get_or_create(data={"created_by_id": bot_user_id})
    print(f"📞 Call created: {call_id}")

    # Open browser for users to join with the user token
    open_browser(client.api_key, user_token, call_id)

    print("\n🤖 Starting transcription bot...")
    print("The bot will join the call and transcribe all audio it receives.")
    print("Join the call in your browser and speak to see transcriptions appear here!")
    print("\nPress Ctrl+C to stop the transcription bot.\n")

    # Initialize Deepgram STT (api_key comes from .env)
    stt = DeepgramSTT()

    try:
        async with await rtc.join(call, bot_user_id) as connection:
            print(f"✅ Bot joined call: {call_id}")

            # Set up transcription handlers
            @connection.on("audio")
            async def on_audio(pcm: PcmData, user):
                # Process audio through Deepgram STT
                await stt.process_audio(pcm, user)

            @stt.on("transcript")
            async def on_transcript(text: str, user: any, metadata: dict):
                timestamp = time.strftime("%H:%M:%S")
                user_info = user if user else "unknown"
                print(f"[{timestamp}] {user_info}: {text}")
                if metadata.get("confidence"):
                    print(f"    └─ confidence: {metadata['confidence']:.2%}")

            @stt.on("partial_transcript")
            async def on_partial_transcript(text: str, user: any, metadata: dict):
                if text.strip():  # Only show non-empty partial transcripts
                    user_info = user if user else "unknown"
                    print(
                        f"    {user_info} (partial): {text}", end="\r"
                    )  # Overwrite line

            @stt.on("error")
            async def on_stt_error(error):
                print(f"\n❌ STT Error: {error}")

            # Keep the connection alive and wait for audio
            print("🎧 Listening for audio... (Press Ctrl+C to stop)")
            await connection.wait()

    except asyncio.CancelledError:
        print("\n⏹️  Stopping transcription bot...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await stt.close()
        client.delete_users([user_id, bot_user_id])
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
