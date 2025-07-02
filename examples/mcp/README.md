# Stream × FastMCP Demo

This folder contains a **complete Stream × FastMCP demo**. Running a *single* script spins up everything you need – the MCP server, the LLM agent and a Stream-Video call bot – and shows the whole tool-calling loop end-to-end.

Run it, talk, and the bot will answer – possibly after calling a tool.

> The supporting files (`server.py`, `agent.py`) are here mostly to show how
> MCP tools are defined and how the agent lets the LLM call them. You don't
> run them directly; `main.py` orchestrates the whole thing for you.

---

## 1 — Prerequisites

• Python ≥ 3.10 (⁠we use `pyproject.toml` to pin the packages)
• A Stream account with API key/secret
• An OpenAI API key
• Deepgram + ElevenLabs keys if you want speech-to-text **and** text-to-speech

Create an `.env` file in this directory (or export the variables any other way):

```env
OPENAI_API_KEY=sk-…

# stream.io credentials
STREAM_API_KEY=…
STREAM_API_SECRET=…

# optional – only needed if you run `main.py`
DEEPGRAM_API_KEY=…
ELEVENLABS_API_KEY=…
```

---

## 2 — Install deps into an isolated venv

We recommend [uv](https://github.com/astral-sh/uv):

```bash
# create a fresh virtual-env in .venv and install everything from pyproject.toml
uv venv .venv
uv pip install -r <(uv pip compile examples/mcp/pyproject.toml)

# or, if you already have uv 0.1.26+
uv sync -q --all-packages -p examples/mcp/pyproject.toml
```

Feel free to use `pip`/`poetry`/`pip-tools` instead; the TOML lists the same deps.

---

## 3 — Run the demo (1-liner)

```bash
uv run examples/mcp/main.py   # or: python examples/mcp/main.py
```

`main.py` will

1. launch the tiny MCP server defined in `server.py`,
2. create a temporary Stream call and open it in your browser,
3. join the call as a bot participant, and
4. feed speech → text → LLM → tools → speech.

Speak in the browser tab. The Deepgram STT engine turns your voice into
text; the LLM decides whether it should answer directly or call a tool (see
the `get_forecast` sample); if it does, the result is fed back to the LLM and
finally read out loud via ElevenLabs.

Stop with `Ctrl-C`. The script tears everything down and removes the temporary
users from your Stream instance.

---

## 4 — Anatomy of the example

| File | Role |
|------|------|
| `server.py` | Shows how to **define MCP tools** with the `@mcp.tool()` decorator. (Launched automatically by `main.py`.) |
| `agent.py` | Very small helper that lets the LLM call tools and loops the results back. Imported by `main.py`. |
| `main.py` | The only file you *run*. Orchestrates the video call, launches the MCP server as a subprocess and drives the agent. |

---

## 5 — Adding your own tools

1.  Edit `server.py` and drop in a regular Python function. Annotate the
    parameters and return type — those become the tool's schema.

   ```python
   @mcp.tool()
   def table_availability(restaurant: str, date: str, seats: int) -> str:
       """Check if *restaurant* has a free table for *seats* people on *date*."""
       # Imagine this hits the booking API for the venue.
       resp = httpx.get(
           "https://api.example.com/availability",
           params={"restaurant": restaurant, "date": date, "seats": seats},
           timeout=5,
       )
       return resp.json()["status"]  # e.g. "available" / "fully booked"
   ```

2.  Restart the demo.  The agent advertises the new tool automatically; the LLM
    can now call `table_availability[{"restaurant": "Pasta Place", "date": "2025-07-01", "seats": 4}]`.
