#!/usr/bin/env python3

import asyncio
import os
import logging
import argparse
from uuid import uuid4
from dotenv import load_dotenv
from aiortc.contrib.media import MediaPlayer

from examples.utils import create_user
from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.rtc.recording import RecordingType

# Configure logging for the Stream SDK
logging.basicConfig(level=logging.WARN)

# Sample audio files - update these paths to your actual audio files
AUDIO_FILES = [
    "/path/to/audio/input1.mp3",
    "/path/to/audio/input2.mp3",
    "/path/to/audio/input3.mp3",
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

        if player.audio:
            print(f"Bot {bot_name} created with audio: {os.path.basename(audio_file)}")
            return bot_user_id, player

        print(f"No audio track found in {audio_file}")
        return None

    except Exception as e:
        print(f"Error creating bot {bot_name}: {e}")
        return None


async def print_recording_status(connection):
    """Print the current recording status."""
    status = connection.get_recording_status()
    print("Recording Status:")
    print(f"   • Recording Active: {status['recording_enabled']}")
    print(f"   • Recording Types: {status['recording_types']}")
    print(f"   • Output Directory: {status['output_directory']}")
    if "user_id_filter" in status:
        print(f"   • User Filter: {status['user_id_filter']}")


async def record(connection, recording_type, output_dir, user_id_filter=None):
    """Perform recording with the specified parameters."""
    print(f"\nStarting {recording_type} recording...")

    # Start recording with specified parameters
    recording_params = {"recording_types": [recording_type], "output_dir": output_dir}
    if user_id_filter:
        recording_params["user_ids"] = user_id_filter

    await connection.start_recording(**recording_params)

    # Show recording status
    await print_recording_status(connection)

    # Record for 20 seconds
    print("\nRecording for 20 seconds...")
    await asyncio.sleep(20)

    # Stop recording
    print("\nStopping recording...")
    await connection.stop_recording()

    # Show final results
    final_status = connection.get_recording_status()
    print("\nRecording Complete!")
    print(f"   • Output Directory: {final_status['output_directory']}")


async def record_composite(recorder_connection, bot_connections):
    """Record composite audio from all participants."""
    await record(
        recorder_connection,
        RecordingType.COMPOSITE,
        "recordings/composite",
        user_id_filter=bot_connections,
    )


async def record_tracks(recorder_connection, bot_connections):
    """Record individual tracks from each participant."""
    await record(
        recorder_connection,
        RecordingType.TRACK,
        "recordings/tracks",
        user_id_filter=bot_connections,
    )


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


async def main():
    """Main recording example with multiple audio file inputs."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Stream Video Recording Example")
    parser.add_argument(
        "--type",
        choices=["composite", "track"],
        required=True,
        help="Type of recording to perform (composite or track)",
    )
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    print(f"Audio Recording Example - {args.type.title()} Recording")
    print("=" * 50)

    # Initialize Stream client
    client = Stream.from_env()

    # Create a unique call
    call_id = f"recording-example-{str(uuid4())}"
    call = client.video.call("default", call_id)
    print(f"Call ID: {call_id}")

    # Create the call
    call.get_or_create(data={"created_by_id": "recording-example"})

    try:
        # Set up bots
        bot_names = ["Alice", "Bob", "Charlie"]
        bot_user_ids, players = await setup_bots(client, bot_names, AUDIO_FILES)
        if not bot_user_ids:
            return

        # Create recorder user
        recorder_user_id = f"bot-recorder-{str(uuid4())[:8]}"
        create_user(client, recorder_user_id, "Recording Bot")

        # Join all bots first and add their tracks
        async with (
            await rtc.join(call, bot_user_ids[0]) as bot1_connection,
            await rtc.join(call, bot_user_ids[1]) as bot2_connection,
            await rtc.join(call, bot_user_ids[2]) as bot3_connection,
        ):
            # Add all audio tracks
            for connection, player in zip(
                [bot1_connection, bot2_connection, bot3_connection], players
            ):
                if player.audio:
                    await connection.add_tracks(audio=player.audio)

            # Now join with recorder and start recording
            async with await rtc.join(call, recorder_user_id) as recorder_connection:
                print(f"Recorder joined: {recorder_user_id}")

                # Run the selected recording type
                if args.type == "composite":
                    await record_composite(
                        recorder_connection,
                        [bot1_connection.user_id],
                    )
                else:  # track recording
                    await record_tracks(
                        recorder_connection,
                        [bot1_connection.user_id],
                    )

                for connection in [bot1_connection, bot2_connection, bot3_connection]:
                    await connection.leave()
                    await asyncio.sleep(1.0)
    except Exception as e:
        print(f"Error during recording: {e}")
    finally:
        # Delete created users
        print("Deleting created users...")
        try:
            # Delete bot users
            client.delete_users(bot_user_ids + [recorder_user_id])
            print("Deleted bot users")
        except Exception as e:
            print(f"Error during user cleanup: {e}")

        print("Done")


if __name__ == "__main__":
    print("Before running this example:")
    print("   1. Update the AUDIO_FILES list with paths to your actual audio files")
    print(
        "   2. Make sure you have a .env file with STREAM_API_KEY and STREAM_API_SECRET"
    )
    print(
        "   3. Audio files should be in a format supported by aiortc (WAV, MP3, MP4, etc.)"
    )
    print("   4. Run with --type composite or --type track to specify recording type")
    print()

    asyncio.run(main())
