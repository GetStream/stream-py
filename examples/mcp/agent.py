import logging
import openai
import fastmcp
import json
import re
import os

logging.basicConfig(level=logging.INFO)

openai.api_key = os.environ["OPENAI_API_KEY"]

SYSTEM = """
You are a friendly AI assistant.  When the user asks for real-world data, look through the
available MCP tools and call the one that matches.  Reply with plain text.
If you call a tool, use  "tool_name"["argument_key": "argument_value"]  on its own line.
You can make up to 3 tool calls in a row.
"""


def call_llm(messages):
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )
    logging.info(f"LLM response: {response}")
    logging.info(f"LLM response content: {response.choices[0].message.content}")
    return response.choices[0].message.content


async def chat_with_tools(prompt: str, client: fastmcp.Client) -> str:
    tools = await client.list_tools()
    tool_descriptions = [f"{t.name}: {t.description}" for t in tools]
    history = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt},
        {
            "role": "assistant",
            "content": "Available tools:\n" + "\n".join(tool_descriptions),
        },
    ]

    while True:
        tool_calls = 0
        reply = call_llm(history)
        m = re.match(r"^(\w[\w\.]+)\[(.*)\]$", reply.strip())

        # If the LLM calls a tool, call it and add the result to the history
        if m and m.group(1) in [t.name for t in tools]:
            tool_name, arg_json = m.groups()
            # Wrap the arguments in braces so they become valid JSON
            args = json.loads("{" + arg_json + "}")
            result = await client.call_tool(tool_name, args)
            history.append({"role": "assistant", "content": f"(result) {result.data}"})
            tool_calls += 1
            if tool_calls == 2:
                history.append(
                    {
                        "role": "assistant",
                        "content": "You can make up to 3 tool calls in a row.  You have already made 2 tool calls.  Please answer the user's question directly.",
                    }
                )
            if tool_calls >= 3:
                return reply
            continue
        else:
            return reply
