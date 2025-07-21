#!/usr/bin/env python3

import logging
import numpy as np
from uuid import uuid4
import aiortc
from dotenv import load_dotenv
from aiortc.contrib.media import MediaPlayer
from google.genai.types import Modality, MediaResolution, TurnCoverage, ActivityHandling

from examples.utils import create_user
from getstream.stream import Stream
from getstream.video import rtc

import asyncio
import os
from pathlib import Path
import webbrowser
from urllib.parse import urlencode

from google import genai
from google.genai import types
import websockets
import pyaudio

from getstream.video.rtc.track_util import PcmData

pya = pyaudio.PyAudio()

initialised = False
g_session = None

# Configure logging for the Stream SDK
logging.basicConfig(level=logging.ERROR)

# Audio playback/recording constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

async def play_audio(audio_in_queue):
    """Play audio from the queue using PyAudio."""
    stream = await asyncio.to_thread(
        pya.open,
        format=FORMAT,
        channels=CHANNELS,
        rate=RECEIVE_SAMPLE_RATE,
        output=True,
    )
    while True:
        bytestream = await audio_in_queue.get()
        await asyncio.to_thread(stream.write, bytestream)

async def gather_responses(session: "genai.aio.live.Session", output: Path, audio_in_queue):
    """Collect model responses and append parsed JSON to output list."""
    buffer = ""
    try:
        while True:
            turn = session.receive()
            async for response in turn:
                if data := response.data:
                    audio_in_queue.put_nowait(data)
                    continue
                if response.server_content.output_transcription:
                    buffer += response.server_content.output_transcription.text
            print(f"\nTranscript: {buffer}")
            with open(output, "a") as f:
                f.write(buffer)
                f.write("\n")
            buffer = ""
            # while not audio_in_queue.empty():
            #     audio_in_queue.get_nowait()
            # await asyncio.sleep(1)
            # await session.send_realtime_input(text="Analyse the video. IF THE POSITION HAS NOT CHANGED, "
            #                                        "DO NOT SAY ANYTHING EVEN IF PROMPTED")
    except websockets.exceptions.ConnectionClosedOK:
        print("Connection closed OK")
    except asyncio.CancelledError:
        print("Connection cancelled")
    except KeyboardInterrupt:
        print("Keyboard interrupt")
    except Exception as e:
        print(f"Error: {e}")
        raise e

async def on_track_added(track_id, track_type, user, ai_connection, audio_in_queue):
    """Handle a new track being added to the ai connection."""
    global g_session
    print(f"VIVEK Track added: {track_id} for user {user} of type {track_type}")
    if track_type != "video" and not g_session:
        return

    track = ai_connection.subscriber_pc.add_track_subscriber(track_id)

    if track:
        if not g_session:
            client = genai.Client(http_options={"api_version": "v1beta"}, api_key=os.getenv("GOOGLE_API_KEY"))
            PROMPT = """
            You are a darts expert.
            You will be given video frames from a darts practice session at 2 frames per second of a single player.
            Analyse the player throwing form and coach him to improve his darts game.
            DO NOT SAY ANYTHING ELSE
            DO NOT PROVIDE ANY OTHER INFORMATION OR REPEAT THE SAME INFORMATION
            DO NOT GREET THE USER BEFORE THE USER SAYS SOMETHING
            DO NOT ASK FOLLOW-UP QUESTIONS
            """

            gemini_config: types.LiveConnectConfig = types.LiveConnectConfig(
                response_modalities=[Modality.AUDIO],
                temperature=0.1,
                system_instruction=PROMPT,
                media_resolution=MediaResolution.MEDIA_RESOLUTION_MEDIUM,
                context_window_compression=types.ContextWindowCompressionConfig(
                    trigger_tokens=25600,
                    sliding_window=types.SlidingWindow(
                        target_tokens=12800
                    )
                ),
                output_audio_transcription=types.AudioTranscriptionConfig(),
                realtime_input_config=types.RealtimeInputConfig(
                    turn_coverage=TurnCoverage.TURN_INCLUDES_ALL_INPUT,
                    activity_handling=ActivityHandling.NO_INTERRUPTION,
                ),
                # proactivity=types.ProactivityConfig(
                #     proactive_audio=True,
                # ),
            )

            async with client.aio.live.connect(
                    model="models/gemini-live-2.5-flash-preview",
                    # model="models/gemini-2.5-flash-live-preview",
                    # model="models/gemini-2.5-flash-preview-native-audio-dialog",
                    config=gemini_config,
            ) as session:
                g_session = session
                asyncio.create_task(gather_responses(session, Path("recordings/texts/analysis.txt"), audio_in_queue))
                asyncio.create_task(play_audio(audio_in_queue))
                # await session.send_realtime_input(text="This is the starting position")
                if track_type == "video":
                    frame_count = 0
                    while True:
                        try:
                            video_frame: aiortc.mediastreams.VideoFrame = await track.recv()

                            # feed to smolVLM/openCV
                            if video_frame:
                                print(f"Video frame received: {video_frame.time}")
                                img = video_frame.to_image()
                                with open(f"recordings/texts/image_{frame_count}.png", "wb") as f:
                                    img.save(f)
                                await session.send_realtime_input(
                                    media=img,
                                )
                                frame_count += 1
                            await asyncio.sleep(1)
                        except Exception as e:
                            print(f"Error receiving track: {e} - {type(e)}")
                            break
    else:
        print(f"Track not found: {track_id}")


# Sample files - update these paths to your actual files
INPUT_FILES = [
    "/Users/vivek/Desktop/darts/darts_coaching_4.mp4",
]

async def create_bot_with_audio(client, bot_name: str, audio_file: str):
    """Create a bot user and prepare its audio player."""
    if not os.path.exists(audio_file):
        print(f"Audio file not found: {audio_file}, skipping bot {bot_name}")
        return None

    # Create bot user
    bot_user_id = f"bot-{bot_name.lower()}-{str(uuid4())[:8]}"

    # Create the user in Stream first using the utility function
    create_user(client, bot_user_id, f"Bot {bot_name}")

    try:
        # Create media player from audio file
        player = MediaPlayer(audio_file, loop=True)

        if player.audio or player.video:
            print(f"Bot {bot_name} created with audio: {os.path.basename(audio_file)}")
            return bot_user_id, player

        print(f"No audio track found in {audio_file}")
        return None

    except Exception as e:
        print(f"Error creating bot {bot_name}: {e}")
        return None

async def setup_bots(client, bot_names, audio_files):
    """Set up bot users with audio files."""
    players = []
    bot_user_ids = []

    print("\nCreating bot users with audio files...")

    # Create all users first
    for bot_name, audio_file in zip(bot_names, audio_files):
        result = await create_bot_with_audio(client, bot_name, audio_file)
        if result:
            bot_user_id, player = result
            bot_user_ids.append(bot_user_id)
            players.append(player)

    if not bot_user_ids:
        print("No bots could be created. Please check your audio file paths.")
        return None, None

    print(f"Created {len(bot_user_ids)} bot users")
    return bot_user_ids, players



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
    base_url = f"{os.getenv('EXAMPLE_BASE_URL')}/join/"
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
    # Load environment variables
    load_dotenv()

    print(f"LLM Live Example")
    print("=" * 50)

    # Initialize Stream client
    client = Stream.from_env()

    # Create a unique call
    call_id = f"video-ai-example-{str(uuid4())}"
    call = client.video.call("default", call_id)
    print(f"Call ID: {call_id}")

    human_id = f"user-{uuid4()}"
    create_user(client, human_id, "Human")
    token = client.create_token(human_id, expiration=3600)

    # Create the call
    call.get_or_create(data={"created_by_id": "ai-example"})

    try:
        # Set up bots
        bot_names = ["test-user"]
        bot_user_ids, players = await setup_bots(client, bot_names, INPUT_FILES)
        if not bot_user_ids:
            return

        # Create ai user
        ai_user_id = f"bot-ai-{str(uuid4())[:8]}"
        create_user(client, ai_user_id, "AI Bot")

        # Join all bots first and add their tracks
        async with (
            await rtc.join(call, bot_user_ids[0]) as bot1_connection,
        ):
            # Now join with ai and start processing
            async with await rtc.join(call, ai_user_id) as ai_connection:
                print(f"AI joined: {ai_user_id}")

                # Create audio queue for playback and model responses
                audio_in_queue = asyncio.Queue()

                # Register the track_added event handler with required context
                from functools import partial
                ai_connection.on(
                    "track_added",
                    lambda track_id, track_type, user: asyncio.create_task(
                        on_track_added(track_id, track_type, user, ai_connection, audio_in_queue)
                    )
                )

                # Add all tracks
                for connection, player in zip(
                    [bot1_connection], players
                ):
                    # if player.audio:
                    #     await connection.add_tracks(audio=player.audio)
                    if player.video:
                        await connection.add_tracks(video=player.video)

                @ai_connection.on("audio")
                async def on_audio(pcm: PcmData, user):
                    if g_session:
                       await g_session.send_realtime_input(
                           audio=types.Blob(
                               data=pcm.samples.astype(np.int16).tobytes(), mime_type="audio/pcm;rate=48000"
                           )
                       )

                open_browser(client.api_key, token, call_id)

                await ai_connection.wait()

                for connection in [bot1_connection]:
                    await connection.leave()
                    await asyncio.sleep(1.0)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Delete created users
        print("Deleting created users...")
        try:
            # Delete bot users
            client.delete_users(bot_user_ids + [ai_user_id])
            print("Deleted bot users")
        except Exception as e:
            print(f"Error during user cleanup: {e}")

        print("Done")


if __name__ == "__main__":
    asyncio.run(main())
