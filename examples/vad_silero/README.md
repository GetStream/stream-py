# Stream × Silero — VAD Bot

Detect when people speak in a Stream Video call.

This minimal example starts a bot that listens to the call, runs every audio
frame through the [Silero VAD](https://github.com/snakers4/silero-vad) model
and prints each speech turn with its duration.

---

## Quick start

```bash
cd examples/vad_silero

# install deps (choose one)
pip install -e .
uv venv .venv && source .venv/bin/activate && uv sync   # fast ⚡️

cp ../stt_deepgram_transcription/env.example .env  # fill STREAM_* keys
python main.py                                    # or: uv -m python main.py
```

Speak in the browser tab – you'll see logs like:

```
🤖 VAD bot starting – speak in the call and watch the console.
📞 Call ready: 7a1f…
[12:03:45] Speech from user-d1e8… — 1.32s
[12:03:49] Speech from user-d1e8… — 0.87s
```

---

## How it works

1. Creates two temporary Stream users (human + `vad-bot-*`).
2. Opens the call URL so you can join immediately.
3. Every incoming PCM frame goes to `Silero.process_audio()`.
4. The plugin emits `partial` (in-progress) and `audio` (end-of-turn) events.
5. On **Ctrl-C** the bot leaves the call and temporary users are deleted.

< 120 lines of Python 🐍 