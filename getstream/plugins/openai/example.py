import asyncio
import os
from typing import Any

from getstream.plugins.openai.llm import OpenAILLM


async def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY in your environment")

    llm = OpenAILLM(api_key=api_key, model="gpt-4.1-mini")

    # Print normalized deltas (text/audio) as they arrive
    def on_delta(event: Any) -> None:
        name = getattr(event, "event_name", None)
        norm = getattr(event, "normalized_delta", None)
        if name == "text.delta" and isinstance(norm, dict):
            text = norm.get("text")
            if isinstance(text, str) and text:
                print("TEXT:", text, flush=True)

    llm.on("delta", on_delta)

    # Non-streaming request
    messages: list[str] = ["Please say hi to the user and ask how their day is."]
    print("Non-streaming create_response...", flush=True)
    resp = await llm.create_response(messages=messages)
    print("Done. Response id:", getattr(resp, "id", None), flush=True)
    print(resp)

    # Streaming request
    messages_stream: list[str] = ["Stream your answer in short sentences."]
    print("Streaming create_response_stream...", flush=True)
    async for _ in llm.create_response_stream(messages=messages_stream):
        pass
    print("Stream completed.", flush=True)

    await llm.close()


if __name__ == "__main__":
    asyncio.run(main())
