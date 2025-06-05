import asyncio
import logging
import os
from uuid import uuid4
from dotenv import load_dotenv
from examples.utils import create_user, open_browser
from getstream import Stream
from getstream.models import StartClosedCaptionsResponse
from getstream.plugins.sts.openai_realtime import OpenAIRealtime
from dataclasses import asdict
import json


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

    try:
        logging.info("Connecting to OpenAI Realtime...")
        
        # Check if API key is set
        if not os.getenv("OPENAI_API_KEY"):
            logging.error("❌ OPENAI_API_KEY not found in environment")
            return
        
        async with await sts_bot.connect(call, agent_user_id=bot_user_id) as connection:
            tools = [
                {
                    "type": "function",
                    "name": "start_closed_captions",
                    "description": "start closed captions for the call",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                }
            ]

            await sts_bot.update_session(
                turn_detection={
                    "type": "semantic_vad",
                    "eagerness": "low",
                    "create_response": True,
                    "interrupt_response": True,
                },
                tools=tools,
            )

            logging.info("🎧 Listening for responses... (Press Ctrl+C to stop)")
            logging.info("💡 Try speaking in the browser – ask it something like 'start closed captions' to trigger the function call.")

            async def start_closed_captions() -> StartClosedCaptionsResponse:
                """Helper that starts closed captions for the call."""
                return call.start_closed_captions().data

            async for event in connection:
                logging.info("🔔 Event received: %s", event.type)

                if (
                    event.type == "response.done"
                    and event.response.output is not None
                    and len(event.response.output) > 0
                    and event.response.output[0].type == "function_call"
                ):
                    tool_call_id = event.response.output[0].call_id
                    
                    if event.response.output[0].name == "start_closed_captions":
                        logging.info("🛠  Assistant requested start_closed_captions()")

                        result = await start_closed_captions()

                        # Send the tool result back to the assistant
                        await sts_bot.send_function_call_output(tool_call_id, result.to_json())

                        logging.info("🛠  Replied to tool call with result: %s", result)

            

    except KeyboardInterrupt:  # noqa: WPS420
        logging.info("\n⏹️  Stopping OpenAI Realtime Speech to Speech bot…")
    except Exception as e:  # noqa: BLE001
        logging.exception("❌ Error: %s", e)
    finally:
        logging.info("Cleaning up...")
        client.delete_users([user_id, bot_user_id])
        logging.info("Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())