# OpenAI Realtime Speech-to-Speech + Stream Video

This example shows how to attach an **OpenAI Realtime** speech-to-speech agent to a Stream Video call.

The agent is able to:

* Join a call as a virtual participant.
* Listen to human speech and reply with synthesized voice in real-time.
* React to **function calls** – in this sample it can start closed-captions on the call when asked ("Start closed captions").

---
## Requirements

| Tool | Purpose |
|------|---------|
| Python ≥ 3.9 | Runtime |
| `uv` *(optional)* | Fast dependency sync – you can also use plain `pip` |
| A **Stream** account | Obtain `STREAM_API_KEY` and `STREAM_API_SECRET` |
| An **OpenAI** account | Obtain `OPENAI_API_KEY` (must have Realtime access) |

---
## Installation

```bash
# 1. Clone the repo and cd in
$ git clone https://github.com/GetStream/stream-py.git
$ cd stream-py

# 2. Set up the environment (pick one)

# ⚡️ Using **uv** (recommended)
$ uv venv .venv                 # create an isolated virtual-env (or omit path to use .venv default)
$ source .venv/bin/activate     # activate it (Fish/Zsh users: use the matching script)
$ uv sync                       # install deps from `pyproject.toml` / `uv.lock`

# 🐍 Classic Python workflow (no uv)
$ python -m venv .venv && source .venv/bin/activate
$ pip install -r requirements.txt
```

---
## Environment variables

Create an **`.env`** file at the repo root (or export vars in your shell):

```dotenv
# Stream credentials
STREAM_API_KEY=xxx
STREAM_API_SECRET=xxx
STREAM_BASE_URL=https://pronto.getstream.io   # default; change if you have a dedicated endpoint

# OpenAI credentials
OPENAI_API_KEY=sk-...
```

---
## Running the demo

### With uv (one-liner)

```bash
$ uv run examples/openai_realtime_speech_to_speech/main.py
```

`uv run` will automatically lock & sync dependencies before launching the script.

### With plain Python

```bash
python examples/openai_realtime_speech_to_speech/main.py
```

The script will:

1. Spin up a temporary Stream Video call.
2. Create two users: *you* and the *OpenAI bot*.
3. Open your default browser on the call URL (auto-join lobby is skipped).
4. Connect the OpenAI Realtime agent to the call with:
   * model `gpt-4o-realtime-preview`
   * voice `alloy`
   * system instructions: "You are a friendly assistant; reply verbally in a short sentence."
5. Wait for audio. Try speaking and then say **"Start closed captions."**
6. The assistant will issue a `start_closed_captions` **function call**. The script intercepts it, calls Stream's `start_closed_captions()` backend method, and returns the result to OpenAI so it can confirm success verbally.

Stop the example with **Ctrl +C**.

---
## File guide

* `main.py` – The runnable example described above.
* `README.md` – (this file) How to run the sample.

For a deeper dive into the STS wrapper see `getstream/plugins/sts/openai_realtime/sts.py`.
