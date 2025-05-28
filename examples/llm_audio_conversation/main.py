#!/usr/bin/env python3
"""
Example: LLM Audio Conversation with Stream, Deepgram STT, and ElevenLabs TTS

This example demonstrates how to:
1. Join a Stream video call
2. Use VAD (Voice Activity Detection) to detect speech
3. Transcribe audio in real-time using Deepgram STT
4. Echo back the transcript using ElevenLabs TTS

Usage:
    python main.py

Requirements:
    - Create a .env file with your Stream, Deepgram, and ElevenLabs credentials
    - Install dependencies: pip install -e .
"""

import asyncio
import os
import time
from typing import Any
from dotenv import load_dotenv

from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.rtc import audio_track
from getstream.plugins.vad.silero import Silero
from getstream.plugins.stt.deepgram import Deepgram
from getstream.plugins.tts.elevenlabs import ElevenLabs
from getstream.video.rtc.track_util import PcmData

from openai import OpenAI
from openai.types.responses.response import Response as OpenAIResponse


async def main():
    """Main example function."""
    load_dotenv()

    print("🎙️  Stream + VAD + Deepgram STT + ElevenLabs TTS Example")
    print("=" * 60)

    # Initialize Stream client from environment variables
    client = Stream.from_env()

    # Create a unique call ID for this session
    call_id = os.getenv("CALL_ID")
    print(f"📞 Call ID: {call_id}")

    bot_user_id = "llm-audio-bot"

    # Create the call
    call = client.video.call("default", call_id)
    call.get_or_create(data={"created_by_id": bot_user_id})
    print(f"📞 Call created: {call_id}")

    # Initialize components
    audio = audio_track.AudioStreamTrack(framerate=16000)
    vad = Silero()
    stt = Deepgram()
    tts_instance = ElevenLabs(voice_id="zOImbcIGBTxd0yXmwgRi")
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    tts_instance.set_output_track(audio)

    print("\n🤖 Starting LLM audio conversation bot...")
    print("The bot will join the call, detect speech, transcribe it, and echo it back.")
    print("\nPress Ctrl+C to stop the bot.\n")

    try:
        async with await rtc.join(call, bot_user_id) as connection:
            await connection.add_tracks(
                audio=audio,
            )

            print(f"✅ Bot joined call: {call_id}")

            await tts_instance.send("welcome my friend, how's it going?")

            @connection.on("audio")
            async def on_audio(pcm: PcmData, user):
                await vad.process_audio(pcm, user)

            @vad.on("audio")
            async def on_speech_detected(pcm: PcmData, user):
                print(
                    f"{time.time()} Speech detected from user: {user} duration {pcm.duration}"
                )
                await stt.process_audio(pcm, user)

            @stt.on("transcript")
            async def on_transcript(text: str, user: Any, metadata: dict[str, Any]):
                print(
                    f"{time.time()} got text from user {user}, with metadata {metadata}"
                    f"will send the transcript to the LLM: {text}"
                )

                response: OpenAIResponse = openai_client.responses.create(
                    model="gpt-4.1",
                    input=f"Respond to the following user message. Be polite and friendly. Here's the message: {text}",
                )

                await tts_instance.send(response.output_text)

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
        # Clean up services
        await stt.close()
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
