#!/usr/bin/env python3
import argparse
import logging
import numpy as np
import traceback
from uuid import uuid4
import aiortc
from dotenv import load_dotenv
from aiortc.contrib.media import MediaPlayer
from google.genai.types import Modality, MediaResolution, TurnCoverage, ActivityHandling

from examples.utils import create_user, open_browser
from getstream.plugins.silero.vad import SileroVAD
from getstream.stream import Stream
from getstream.video import rtc

import asyncio
import os
from pathlib import Path

from google import genai
from google.genai import types
import websockets
import pyaudio

from getstream.video.call import Call
from getstream.video.rtc.track_util import PcmData
from getstream.video.rtc.audio_track import AudioStreamTrack

pya = pyaudio.PyAudio()

initialised = False
g_session = None

# Configure logging for the Stream SDK
logging.basicConfig(level=logging.ERROR)

# Audio playback/recording constants
RECEIVE_SAMPLE_RATE = 24000

INPUT_FILE = ""

async def play_audio(audio_in_queue, ai_connection):
    """Play audio from the queue using PyAudio."""
    audio = AudioStreamTrack(framerate=RECEIVE_SAMPLE_RATE, stereo=False, format="s16")
    await ai_connection.add_tracks(audio=audio)
    while True:
        bytestream = await audio_in_queue.get()
        await audio.write(bytestream)

async def gather_responses(session: "genai.aio.live.Session", output: Path, audio_in_queue):
    """Collect model responses and append parsed JSON to output list."""
    output_buffer = ""
    input_buffer = ""
    try:
        while True:
            turn = session.receive()
            async for response in turn:
                if data := response.data:
                    audio_in_queue.put_nowait(data)
                    continue
                if response.server_content.input_transcription:
                    input_buffer += response.server_content.input_transcription.text
                if response.server_content.output_transcription:
                    output_buffer += response.server_content.output_transcription.text
            print(f"\nInput transcript: {input_buffer}")
            print(f"\nOutput transcript: {output_buffer}")
            if args.debug:
                with open(output, "a") as f:
                    f.write(output_buffer)
                    f.write("\n")
            output_buffer = ""
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

async def on_track_added(track_id, track_type, user, target_user_id, ai_connection, audio_in_queue):
    """Handle a new track being added to the ai connection."""
    global g_session
    print(f"Track added: {track_id} for user {user} of type {track_type}")
    if track_type != "video" and not g_session:
        return
    if user.user_id != target_user_id:
        print(f"User {target_user_id} does not belong to user {user.user_id}")
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
                input_audio_transcription=types.AudioTranscriptionConfig(),
                output_audio_transcription=types.AudioTranscriptionConfig(),
                realtime_input_config=types.RealtimeInputConfig(
                    turn_coverage=TurnCoverage.TURN_INCLUDES_ALL_INPUT,
                    # activity_handling=ActivityHandling.NO_INTERRUPTION,
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
                asyncio.create_task(gather_responses(session, Path("debug/analysis.txt"), audio_in_queue))
                asyncio.create_task(play_audio(audio_in_queue, ai_connection))
                # await session.send_realtime_input(text="This is the starting position")
                if track_type == "video":
                    frame_count = 0
                    while True:
                        try:
                            video_frame: aiortc.mediastreams.VideoFrame = await track.recv()
                            if video_frame:
                                print(f"Video frame received: {video_frame.time} - {video_frame.format}")
                                img = video_frame.to_image()
                                if args.debug:
                                    with open(f"debug/image_{frame_count}.png", "wb") as f:
                                        img.save(f)
                                await session.send_realtime_input(
                                    media=img,
                                )
                                frame_count += 1
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            print(f"Error receiving track: {e} - {type(e)}")
                            break
    else:
        print(f"Track not found: {track_id}")

async def publish_media(call: Call, user_id: str, player: MediaPlayer):
    try:
        async with await rtc.join(call, user_id) as connection:
            await connection.add_tracks(audio=player.audio, video=player.video)

            await connection.wait()
    except Exception as e:
        print(f"Error: {e} - stacktrace: {traceback.format_exc()}")

async def main():

    print(f"LLM Live Example")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    input_media_player = None

    if INPUT_FILE != "":
        if not os.path.exists(INPUT_FILE):
            print(f"Input file not found: {INPUT_FILE}")
            return None
        input_media_player = MediaPlayer(INPUT_FILE, loop=False)
        if not (input_media_player.audio or input_media_player.video):
            print("No audio/video track found in input file")
            return None

    # Initialize Stream client
    client = Stream.from_env()

    # Create a unique call
    call_id = f"video-ai-example-{str(uuid4())}"
    call = client.video.call("default", call_id)
    print(f"Call ID: {call_id}")

    viewer_user_id = f"viewer-{uuid4()}"
    player_user_id = f"player-{str(uuid4())[:8]}"
    ai_user_id = f"ai-{str(uuid4())[:8]}"

    create_user(client, player_user_id, "Player")
    if input_media_player:
        create_user(client, viewer_user_id, "Viewer")
        token = client.create_token(viewer_user_id, expiration=3600)
    else:
        token = client.create_token(player_user_id, expiration=3600)
    create_user(client, ai_user_id, "AI Bot")

    # Create the call
    call.get_or_create(data={"created_by_id": "ai-example"})

    try:
        # vad = SileroVAD()

        # Join all bots first and add their tracks
        async with await rtc.join(call, ai_user_id) as ai_connection:            
            # Create audio queue for playback and model responses
            audio_in_queue = asyncio.Queue()
            ai_connection.on(
                "track_added",
                lambda track_id, track_type, user: asyncio.create_task(
                    on_track_added(track_id, track_type, user, player_user_id, ai_connection, audio_in_queue)
                )
            )

            #
            # async def _on_pcm(pcm: PcmData, user):
            #     if user.user_id == player_user_id:
            #         await vad.process_audio(pcm, user)

            # @vad.on("audio")
            @ai_connection.on("audio")
            async def on_audio(pcm: PcmData, user):
                if user.user_id == player_user_id and g_session:
                    await g_session.send_realtime_input(
                        audio=types.Blob(
                            data=pcm.samples.astype(np.int16).tobytes(), mime_type="audio/pcm;rate=48000"
                        )
                    )
            
            open_browser(client.api_key, token, call_id)

            await asyncio.sleep(2)

            if input_media_player:
                asyncio.create_task(publish_media(call, player_user_id, input_media_player))

            await ai_connection.wait()
    except Exception as e:
        print(f"Error: {e} - stacktrace: {traceback.format_exc()}")
    finally:
        # Delete created users
        print("Deleting created users...")
        client.delete_users([player_user_id, ai_user_id, viewer_user_id])

    return None

if __name__ == "__main__":
    # Parse command line arguments
    args_parser = argparse.ArgumentParser(description="Video AI Example")
    args_parser.add_argument(
        "-i", "--input-file",
        required = False,
        help = "Input file with video and audio tracks to publish. " \
        "If an input file is specified, it will be used. Otherwise, " \
        "the bot will wait till a video track is published",
    )
    args_parser.add_argument(
        "-d", '--debug',
        action='store_true',
        help="Enable debug mode"
    )
    args = args_parser.parse_args()
    if args.input_file and args.input_file != "" and os.path.exists(args.input_file):
        INPUT_FILE = args.input_file
    if args.debug:
        os.makedirs("debug", exist_ok=True)
    asyncio.run(main())
