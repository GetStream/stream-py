import asyncio
from dotenv import load_dotenv
from uuid import uuid4
import logging

from gpt_realtime import GPTRealtime
from utils import create_user, open_browser

from getstream import Stream
from getstream.video.rtc import join

logging.basicConfig(level=logging.INFO)

async def main():
    load_dotenv()
    client = Stream.from_env()
    user_id = f"user-{uuid4()}"
    gpt_id = f"gpt-{uuid4()}"

    create_user(client, user_id, "User")
    create_user(client, gpt_id, "GPT-Realtime")

    token = client.create_token(user_id, expiration=3600)

    call_id = str(uuid4())
    call = client.video.call("default", call_id)
    call.get_or_create(data={"created_by_id": gpt_id})

    logging.info("Call ready: %s", call_id)

    open_browser(client.api_key, token, call_id)

    logging.info("Waiting for browser to open...")
    await asyncio.sleep(5)
    gpt_realtime = GPTRealtime()

    async with await join(call, gpt_id) as connection:
        @connection.on("track_added")
        async def on_track_added(track_id, kind, _):
            logging.info("Track added: %s", track_id)
            if kind == "audio":
                logging.info("Audio track added: %s", track_id)
                if not gpt_realtime.session_created_event.is_set():
                    track = connection.subscriber_pc.add_track_subscriber(track_id)
                    # Start the GPT WebRTC session
                    await gpt_realtime.start_session(track)
                    await connection.add_tracks(audio=gpt_realtime.audio_track)
            elif kind == "video":
                logging.info("Video track added: %s", track_id)

        await connection.wait()

if __name__ == "__main__":
    asyncio.run(main())
