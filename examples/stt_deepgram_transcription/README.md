# Stream × Deepgram — Real-time Call Transcription

Tiny example that lets a bot join a Stream video call and print live (and partial) transcripts from Deepgram.

## What you'll see

• A browser tab opens on the Stream call interface
• A bot joins automatically
• Everything you say in the call appears in the terminal with timestamps + confidence

Press **Ctrl +C** to stop; the script cleans up the bot, user and Deepgram session for you.

---

## Quick start

### 1. Clone & navigate

```bash
git clone https://github.com/GetStream/stream-py.git
cd stream-video-python/examples/stt_deepgram_transcription
```

### 2. Install deps

Choose **either** flow:

• Classic `pip`

```bash
pip install -e .
```

• Speedy `uv` (no *uv pip*!)

```bash
# create an env
uv venv .venv
source .venv/bin/activate

# install inside the env
uv sync
```

### 3. Configure env vars

```bash
cp env.example .env  # then edit with your STREAM_* + DEEPGRAM_API_KEY
```

### 4. Run it

```bash
python main.py          # or inside uv env ->  uv -m python main.py
```

You'll see something like:

```text
🎙️  Stream + Deepgram Real-time Transcription Example
📞 Call ID: 5e2d…
🔑 Created token for user: user-6a13…
🤖 Created bot user: transcription-bot-1ce7…
✅ Bot joined call: 5e2d…
🎧 Listening for audio… (Ctrl+C to stop)
[18:42:10] user-6a13…: Hello world
    └─ confidence: 99.32%
```

---

## How it works (30 sec tour)

1. `main.py` creates *two* temporary Stream users (human + bot) via `create_user()` and a fresh `call_id`.
2. A browser URL is built with the human user's JWT so you can join instantly.
3. The bot joins the call with `rtc.join()` and wires up event handlers:
   • `audio` → pass raw PCM frames to Deepgram.
   • `transcript` / `partial_transcript` → print results.
4. The `await connection.wait()` line keeps the coroutine alive until you hit **Ctrl +C**.
5. `asyncio.CancelledError` is caught → `finally:` closes Deepgram + deletes the temporary users.

That's it – less than 120 lines of code.

---

## Need help?

• Stream Video docs – <https://getstream.io/video/docs/>
• Deepgram docs – <https://developers.deepgram.com/>
• GitHub Issues – open one on <https://github.com/GetStream/stream-video-python>
