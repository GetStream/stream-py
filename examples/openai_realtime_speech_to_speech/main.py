import asyncio
import logging
import os
from uuid import uuid4
from dotenv import load_dotenv
from examples.utils import create_user, open_browser
from getstream import Stream
from getstream.plugins.sts.openai_realtime import OpenAIRealtime


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,  # Override any previous basicConfig calls
)

# Enable verbose logging for the OpenAI Realtime plugin
logging.getLogger("getstream.plugins.sts.openai_realtime.sts").setLevel(logging.INFO)


async def main():
    """Run a demo call with an OpenAI Speech-to-Speech agent attached."""

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    # Initialize Stream client from env vars (STREAM_API_KEY / SECRET / BASE_URL)
    client = Stream.from_env()

    user_id = f"user-{uuid4()}"
    create_user(client, user_id, "My User")
    logging.info("👤 Created user: %s", user_id)

    user_token = client.create_token(user_id, expiration=3600)
    logging.info("🔑 Created token for user: %s", user_id)

    bot_user_id = f"openai-realtime-speech-to-speech-bot-{uuid4()}"
    create_user(client, bot_user_id, "OpenAI Realtime Speech to Speech Bot")
    logging.info("🤖 Created bot user: %s", bot_user_id)

    call_id = str(uuid4())
    logging.info("📞 Call ID: %s", call_id)

    call = client.video.call("default", call_id)
    call.get_or_create(data={"created_by_id": bot_user_id})
    logging.info("📞 Call created: %s", call_id)

    # Open demo browser so you can join from the UI
    open_browser(client.api_key, user_token, call_id)

    sts_bot = OpenAIRealtime(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-realtime-preview",
        instructions="You are a friendly assistant; reply verbally in a short sentence.",
        voice="alloy",
    )

    @sts_bot.on("connected")
    async def _on_connected():
        print("✅ CONNECTED EVENT RECEIVED")
        logging.info("✅ Bot connected successfully")

    @sts_bot.on("disconnected")
    async def _on_disconnected():
        print("❌ DISCONNECTED EVENT RECEIVED")
        logging.info("❌ Bot disconnected")

    @sts_bot.on("error")
    async def _on_error(error):
        print(f"💥 ERROR EVENT RECEIVED: {error}")
        logging.error("💥 Bot error: %s", error)

    @sts_bot.on("session.created")
    @sts_bot.on("session.updated")
    @sts_bot.on("conversation.item.created")
    @sts_bot.on("response.created")
    @sts_bot.on("response.done")
    @sts_bot.on("call.session_participant_joined")
    @sts_bot.on("call.session_participant_left")
    async def _on_openai_event(event):
        print(f"🔔 Event received: {event.type}")
        print(f"   Event data: {event}")
        logging.info("🔔 Event: %s", event.type)

    try:
        logging.info("Connecting to OpenAI Realtime...")
        
        # Check if API key is set
        if not os.getenv("OPENAI_API_KEY"):
            logging.error("❌ OPENAI_API_KEY not found in environment")
            return
        
        await sts_bot.connect(call, agent_user_id=bot_user_id)
        logging.info("🎧 Listening for responses... (Press Ctrl+C to stop)")
        logging.info("💡 Try speaking in the browser to generate audio events!")

        while sts_bot.is_connected:
            await asyncio.sleep(1)

    except KeyboardInterrupt:  # noqa: WPS420
        logging.info("\n⏹️  Stopping OpenAI Realtime Speech to Speech bot…")
    except Exception as e:  # noqa: BLE001
        logging.exception("❌ Error: %s", e)
    finally:
        logging.info("Cleaning up...")
        await sts_bot.close()
        client.delete_users([user_id, bot_user_id])
        logging.info("Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())