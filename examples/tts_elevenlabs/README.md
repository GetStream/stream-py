# Stream × ElevenLabs — TTS Bot

Speak into a Stream video call… from Python!

This tiny example spins up a text-to-speech bot that joins a call and greets participants using [ElevenLabs](https://elevenlabs.io/) voices.

---

## Quick start

```bash
# clone and move into the repo (if not already there)
cd examples/tts_elevenlabs

# install deps (pick one)
pip install -e .            # classic
uv venv .venv && source .venv/bin/activate && uv sync   # fast ⚡️

# copy env template and fill in keys
cp ../stt_deepgram_transcription/env.example .env
$EDITOR .env                # STREAM_* + ELEVENLABS_API_KEY

# run it
python main.py              # or: uv -m python main.py
```

You'll see the bot join, say a greeting, then wait. Add extra `await tts.send("...")` calls in `main.py` to make it speak more.

---

## How it works (60 sec)

1. Creates two temporary Stream users (human + "tts-bot").
2. Opens a browser URL so you can join the call instantly.
3. Builds an `AudioStreamTrack` and connects it to `ElevenLabs`.
4. Joins the call and sends a greeting via `tts.send()`.
5. `await connection.wait()` keeps the bot alive until **Ctrl-C**.
6. On shutdown the script deletes the temporary users.

Under 120 lines of code 😀

---

Need help? → [Stream Video docs](https://getstream.io/video/docs/) · [ElevenLabs docs](https://docs.elevenlabs.io) 