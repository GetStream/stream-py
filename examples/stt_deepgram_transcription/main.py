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
import time
import uuid
import webbrowser
from dotenv import load_dotenv
from urllib.parse import urlencode

from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.rtc.track_util import PcmData
from getstream.plugins.stt.deepgram import Deepgram


def open_browser(api_key: str, token: str) -> str:
    """
    Helper function to open browser with Stream call link.

    Args:
        api_key: Stream API key
        token: JWT token for the user

    Returns:
        The URL that was opened
    """
    base_url = "https://pronto.getstream.io/bare/join/"
    params = {"api_key": api_key, "token": token}

    url = f"{base_url}?{urlencode(params)}"
    print(f"Opening browser to: {url}")

    try:
        webbrowser.open(url)
        print("Browser opened successfully!")
    except Exception as e:
        print(f"Failed to open browser: {e}")
        print(f"Please manually open this URL: {url}")

    return url


async def main():
    load_dotenv()
    """Main example function."""
    print("🎙️  Stream + Deepgram Real-time Transcription Example")
    print("=" * 55)

    # Initialize Stream client
    client = Stream.from_env()

    # Create a unique call ID for this session
    call_id = f"transcription-demo-{uuid.uuid4().hex[:8]}"
    print(f"📞 Call ID: {call_id}")

    # Create a token for a user to join the call from browser
    user_id = "browser-user"
    user_token = client.create_token(user_id=user_id)
    print(f"🔑 Created token for browser user: {user_id}")

    # Create a token for the transcription bot
    bot_user_id = "transcription-bot"
    client.create_token(user_id=bot_user_id)
    print(f"🤖 Created token for bot user: {bot_user_id}")

    # Create the call
    call = client.video.call("default", call_id)
    call.get_or_create(data={"created_by_id": bot_user_id})
    print(f"📞 Call created: {call_id}")

    # Open browser for users to join with the user token
    open_browser(client.api_key, user_token)

    print("\n🤖 Starting transcription bot...")
    print("The bot will join the call and transcribe all audio it receives.")
    print("Join the call in your browser and speak to see transcriptions appear here!")
    print("\nPress Ctrl+C to stop the transcription bot.\n")

    # Initialize Deepgram STT (api_key comes from .env)
    stt = Deepgram()

    try:
        async with await rtc.join(call, bot_user_id) as connection:
            print(f"✅ Bot joined call: {call_id}")

            # Set up transcription handlers
            @connection.on("audio")
            async def on_audio(pcm: PcmData, user):
                # Process audio through Deepgram STT
                await stt.process_audio(pcm, user)

            @stt.on("transcript")
            async def on_transcript(text: str, user):
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] {user}: {text}")

            # Keep the connection alive and wait for audio
            print("🎧 Listening for audio... (Press Ctrl+C to stop)")
            await connection.wait()

    except KeyboardInterrupt:
        print("\n⏹️  Stopping transcription bot...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Clean up STT service
        await stt.close()
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
