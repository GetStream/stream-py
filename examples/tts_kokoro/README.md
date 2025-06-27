# Stream × Kokoro — TTS Bot

Speak into a Stream video call… from Python!

This tiny example spins up a text-to-speech bot that joins a call and greets participants using the open-weight [Kokoro](https://github.com/hexgrad/kokoro) model.

---

## Quick start

```bash
# clone and move into the repo (if not already there)
cd examples/tts_kokoro

# install deps (pick one)
pip install -e .            # classic
uv venv .venv && source .venv/bin/activate && uv sync   # fast ⚡️

# copy env template and fill in Stream keys
cp ../stt_deepgram_transcription/env.example .env
$EDITOR .env                # STREAM_*

# make sure espeak-ng is installed (macOS example)
brew install espeak-ng

# The example will auto-bootstrap pip if it's missing; this command is a
# manual fallback in case you want to do it yourself upfront.
python -m ensurepip --upgrade  # optional

# run it
python main.py              # or: uv -m python main.py
```

You'll see the bot join, say a greeting, then wait. Add extra `await tts.send("…")` calls in `main.py` to make it speak more.

---

## How it works (60 sec)

1. Creates two temporary Stream users (human + `tts-bot`).
2. Opens a browser URL so you can join the call instantly.
3. Builds an `AudioStreamTrack` at **24 kHz** and connects it to Kokoro.
4. Joins the call and sends a greeting via `tts.send()`.
5. `await connection.wait()` keeps the bot alive until **Ctrl-C**.
6. On shutdown the script deletes the temporary users.

Under 120 lines of code 😀

---

Need help? → [Stream Video docs](https://getstream.io/video/docs/) · [Kokoro README](https://github.com/hexgrad/kokoro/blob/main/README.md) 