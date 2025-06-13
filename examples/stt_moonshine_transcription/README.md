# Stream × Moonshine + Silero — Live Transcription

This example spins up a bot that joins a Stream Video call, detects speech
with **Silero VAD**, transcribes it with the **Moonshine** model, and prints
final transcripts to the terminal.

Pipeline:
```
    WebRTC audio ▶︎ Silero VAD  ▶︎ Moonshine STT  ▶︎ print transcript
```

---

## Quick start

```bash
cd examples/stt_moonshine_transcription

# create & activate env (fast, no pip)
uv venv .venv && source .venv/bin/activate

# install everything declared in this folder's pyproject.toml
uv sync

# copy credentials and run
cp env.example .env   # fill STREAM_* keys
python main.py        # or: uv run python main.py
```

You'll see something like:

```text
🌙  Stream + Moonshine Real-time Transcription Example
📞 Call ID: 4b12…
✅ Bot joined call: 4b12…
🎧 Listening for audio… (Press Ctrl+C to stop)
🎤 Speech detected from user: My User, duration: 1.12s
[14:03:27] My User: hello moonshine
```

---

## How it works (short version)

`main.py` does the following:

1. Creates two temporary users (`create_user`) – **human** and **moonshine-bot**.
2. Generates a random `call_id`, creates the call, and opens a join URL in your browser.
3. Initialises:
   * `Silero()` – voice-activity detector (48 kHz by default).
   * `Moonshine()` – STT model (base or tiny, picked in the plugin).
4. Joins the call with `rtc.join()`, then:

```python
@connection.on("audio")
async def on_pcm(pcm, user):
    await vad.process_audio(pcm, user)  # silence filtered here

@vad.on("audio")
async def on_speech(pcm, user):
    await stt.process_audio(pcm, user)
```

5. `Moonshine` emits a final `transcript` event which is printed with a timestamp.
6. On **Ctrl-C** the script closes the STT client, VAD and deletes the temporary users.

---

Need help?
* Stream Video docs – <https://getstream.io/video/docs/>
* Silero VAD – <https://github.com/snakers4/silero-vad>
* Moonshine model – <https://github.com/usefulsensors/moonshine>
