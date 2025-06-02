#!/usr/bin/env python3
"""
Example: OpenAI Realtime Speech to Speech with Stream

This example demonstrates how to use OpenAI's realitme speech-to-speech model with the Stream Python SDK.

Usage:
    python main.py
"""

import asyncio
import os
import time
from uuid import uuid4

from dotenv import load_dotenv

from examples.utils import create_user, open_browser
from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.rtc import audio_track
from getstream.video.rtc.track_util import PcmData
from getstream.video.openai import get_openai_realtime_client


async def main():
    """Main example function."""
    # Load environment variables from the parent directory (examples/.env)
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    print("🎙️  Stream + OpenAI Realtime Speech to Speech Example")
    print("=" * 60)

    # Initialize Stream client from environment variables
    client = Stream.from_env()

    # Create a user
    id = f"user-{str(uuid4())}"
    create_user(client, id, "My User")
    print(f"👤 Created user: {id}")
    user_token = client.create_token(id, expiration=3600)
    print(f"🔑 Created token for user: {id}")

    # Create a bot user
    bot_user_id = f"openai-realtime-speech-to-speech-bot-{str(uuid4())}"
    create_user(client, bot_user_id, "OpenAI Realtime Speech to Speech Bot")
    print(f"🤖 Created bot user: {bot_user_id}")

    # Create a unique call ID for this session
    call_id = str(uuid4())
    print(f"📞 Call ID: {call_id}")

    # Create the call
    call = client.video.call("default", call_id)
    call.get_or_create(data={"created_by_id": bot_user_id})
    print(f"📞 Call created: {call_id}")

    open_browser(client.api_key, user_token, call_id)

    # Initialize components
    audio = audio_track.AudioStreamTrack(framerate=16000)

    print("\n🤖 Starting OpenAI Realtime Speech to Speech bot...")
    print("The bot will join the call, detect speech, and convert it to speech.")
    print("\nPress Ctrl+C to stop the bot.\n")

    try:
        async with await rtc.join(call, bot_user_id) as connection:
            await connection.add_tracks(
                audio=audio,
            )

            print(f"✅ Bot joined call: {call_id}")

            @connection.on("audio")
            async def on_audio(pcm: PcmData, user):
                print(
                    f"{time.time()} Speech detected from user: {user} duration {pcm.duration}"
                )

            openai_client = get_openai_realtime_client(
                os.getenv("OPENAI_API_KEY"), os.getenv("STREAM_BASE_URL")
            )

            openai_client.responses.create(
                model="gpt-4o-realtime-speech-to-speech",
                input="You are a helpful and friendly assistant. Respond to the user's message in a conversational way. Here's the message:",
            )

            # Keep the connection alive
            print("🎧 Listening for audio... (Press Ctrl+C to stop)")
            await connection.wait()

    except KeyboardInterrupt:
        print("\n⏹️  Stopping LLM audio conversation bot...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Delete users
        client.delete_users([id, bot_user_id])

        # Clean up services
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
