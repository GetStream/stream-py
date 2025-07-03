import logging

from dotenv import load_dotenv
from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.call import Call
from getstream.plugins.deepgram.stt import DeepgramSTT
from getstream.plugins.elevenlabs.tts import ElevenLabsTTS
from getstream.video.rtc import audio_track
from getstream.video.rtc.track_util import PcmData
from examples.mcp.agent import chat_with_tools
import asyncio
import fastmcp
from examples.utils import create_user, open_browser
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


async def run_bot(call: Call, bot_user_id: str):
    """Join the call as a bot, convert speech→text, call MCP tools
    when the transcript is final, then speak the answer back."""

    stt = DeepgramSTT()
    tts = ElevenLabsTTS()
    track = audio_track.AudioStreamTrack(framerate=16000)
    tts.set_output_track(track)

    try:
        # The bot itself joins as a participant so we can receive audio
        async with await rtc.join(call, bot_user_id) as connection:
            await connection.add_tracks(audio=track)
            logging.info("🤖 Bot joined the call and is now listening")

            async with fastmcp.Client("./examples/mcp/server.py") as mcp_client:

                @connection.on("audio")
                async def on_audio(pcm: PcmData, user):
                    """Pipe raw PCM into the STT engine."""
                    await stt.process_audio(pcm, user)

                @stt.on("transcript")
                async def on_transcript(text: str, user: any, metadata: dict):
                    """Handle **final** transcripts only."""
                    if not metadata.get("is_final", False):
                        return

                    logging.info("🗣️  %s: %s", user or "unknown", text)

                    # Ask the LLM; it may decide to call an MCP tool.
                    answer = await chat_with_tools(text, mcp_client)
                    if answer:
                        logging.info("🤖 Bot reply: %s", answer)
                        await tts.send(answer)

                @stt.on("error")
                async def on_stt_error(error):
                    logging.error("STT error: %s", error)

                logging.info("🎧 Bot is listening… (Ctrl-C to stop)")
                await connection.wait()  # run until the program is stopped
    except asyncio.CancelledError:
        print("\n⏹️  Stopping transcription bot...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await stt.close()


async def main():
    """Entry point for the Stream + FastMCP example."""
    print("🎙️  Stream MCP Example")
    print("=" * 55)

    load_dotenv()

    client = Stream.from_env()

    call_id = str(uuid.uuid4())
    print(f"📞 Call ID: {call_id}")

    # Create a regular human user
    user_id = f"user-{uuid.uuid4()}"
    create_user(client, user_id, "Human User")
    user_token = client.create_token(user_id, expiration=3600)

    # Create the bot user that will join
    bot_user_id = f"mcp-bot-{uuid.uuid4()}"
    create_user(client, bot_user_id, "MCP Bot")

    # Initialise the call
    call = client.video.call("default", call_id)
    call.get_or_create(data={"created_by_id": bot_user_id})
    print(f"📞 Call created: {call_id}")

    # Open browser for users to join with the user token
    open_browser(client.api_key, user_token, call_id)

    try:
        await run_bot(call, bot_user_id)
    finally:
        client.delete_users([user_id, bot_user_id])
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
