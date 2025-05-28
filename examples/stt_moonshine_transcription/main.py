#!/usr/bin/env python3
"""
Example: Real-time Call Transcription with Moonshine STT

This example demonstrates how to:
1. Join a Stream video call
2. Transcribe audio in real-time using Moonshine
3. Open a browser link for users to join the call

Usage:
    python main.py

Requirements:
    - Create a .env file with your Stream credentials (see env.example)
    - Install dependencies: pip install -e .
"""

import asyncio
import time
import uuid
import webbrowser
from dotenv import load_dotenv
from urllib.parse import urlencode

from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.rtc.track_util import PcmData
from getstream.plugins.stt.moonshine import Moonshine
from getstream.plugins.vad.silero import Silero


def open_browser(api_key: str, token: str, call_id: str) -> str:
    """
    Helper function to open browser with Stream call link.

    Args:
        api_key: Stream API key
        token: JWT token for the user
        call_id: ID of the call

    Returns:
        The URL that was opened
    """
    base_url = "https://pronto.getstream.io/bare/join/"
    params = {"api_key": api_key, "token": token, "skip_lobby": "true"}

    url = f"{base_url}{call_id}?{urlencode(params)}"
    print(f"Opening browser to: {url}")

    try:
        webbrowser.open(url)
        print("Browser opened successfully!")
    except Exception as e:
        print(f"Failed to open browser: {e}")
        print(f"Please manually open this URL: {url}")

    return url


async def main():
    """Main example function."""
    print("🌙 Stream + Moonshine Real-time Transcription Example")
    print("=" * 55)

    # Load environment variables
    load_dotenv()

    # Initialize Stream client from ENV
    client = Stream.from_env()

    # Create a unique call ID for this session
    call_id = str(uuid.uuid4())
    print(f"📞 Call ID: {call_id}")

    # Create a token for a user to join the call from browser
    user_id = "browser-user"
    user_token = client.create_token(user_id=user_id)
    print(f"🔑 Created token for browser user: {user_id}")

    # Create a token for the transcription bot
    bot_user_id = "transcription-bot"
    print(f"🤖 Created token for bot user: {bot_user_id}")

    # Create the call
    call = client.video.call("default", call_id)
    call.get_or_create(data={"created_by_id": bot_user_id})
    print(f"📞 Call created: {call_id}")

    # Open browser for users to join with the user token
    open_browser(client.api_key, user_token, call_id)

    print("\n🤖 Starting transcription bot...")
    print("The bot will join the call and transcribe speech using VAD + Moonshine STT.")
    print("VAD will filter out silence and only process actual speech.")
    print("Join the call in your browser and speak to see transcriptions appear here!")
    print("\nPress Ctrl+C to stop the transcription bot.\n")

    # Initialize Moonshine STT
    print("🌙 Initializing Moonshine STT...")
    stt = Moonshine()

    # Initialize Silero VAD for speech detection
    print("🔊 Initializing Silero VAD...")
    vad = Silero()
    print("✅ Audio processing pipeline ready: VAD → Moonshine STT")

    async with await rtc.join(call, bot_user_id) as connection:
        print(f"✅ Bot joined call: {call_id}")

        # Set up audio processing pipeline: Audio -> VAD -> STT
        @connection.on("audio")
        async def on_audio(pcm: PcmData, user):
            # Process audio through VAD first to detect speech
            await vad.process_audio(pcm, user)

        @vad.on("audio")
        async def on_speech_detected(pcm: PcmData, user):
            print(
                f"🎤 Speech detected from user: {user.name}, duration: {pcm.duration:.2f}s"
            )
            # Forward detected speech to Moonshine STT
            await stt.process_audio(pcm, user)

        @stt.on("transcript")
        async def on_transcript(text: str, user: any, metadata: dict):
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {user.name}: {text}")

        @stt.on("error")
        async def on_stt_error(error):
            print(f"\n❌ STT Error: {error}")

        # Keep the connection alive and wait for audio
        print("🎧 Listening for audio... (Press Ctrl+C to stop)")
        await connection.wait()

    # Clean up STT and VAD services
    await stt.close()
    await vad.close()
    print("🧹 Cleanup completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Stopping transcription bot...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
