# v1-beta

- [ ] Code generation for Twirp and Protobuf events
- [ ] Basic WS client
- [ ] Send audio/video from files
- [ ] Receive audio
- [ ] Receive video
- [ ] Send VP8
- [ ] VP8 support
- [ ] h.264 support
- [ ] VAD
- [ ] STT example
- [ ] TTS example
- [ ] Computer vision example
- [ ] Speech-to-speech agent example
- [ ] Stable Agent API

# v1

- [ ] WS connection monitoring and reconnection
- [ ] ICE Restart handling
- [ ] Session migrations
- [ ] pypi package
- [ ] Move ICE gather step to SFU (support without trickle)
- [ ] Remove peer connection bundling hack from Python and move to SFU
- [ ] Make connection.add_tracks wait correctly for the track to be ready

# v2

- [ ] Simulcast support
- [ ] DTX
- [ ] Opus RED
- [ ] AV1 decode support
- [ ] VP9 decode support
- [ ] Send RTC stats to SFU


## Agents as recv/send classes

## Pipeline spec

```python
agent = pipeline.Pipeline()

with call.join() as connection:
    # media input gets all events from connection and ingest them into the pipeline
    pipeline.add(media_input(connection))

    # a VAD handles "audio" events from the connection and emits "audio" events that contain speech
    vad = vad.Silero(option={})
    agent.add(vad)

    # a TTS step handles "speech.audio" events and emits "speech.text" events
    tts = whisper.Whisper(options={})
    agent.add(tts)

    # a simple LLM gets a "speech.text" event and creates "speech.text" events
    llm = gemini.LLM(call=call, tools=[])
    agent.add(llm)

    # a TTS gets a "speech.text" event and creates a "audio" event
    tts = elevenlabs.TTS()
    agent.add(tts)

    agent.add(audio_sink(connection))
    await pipeline.run()
```

each arg is a step in the pipeline. the way it works

- each arg in connected to the previous step and will bind to a list of event types
- steps should use pyee for the on() and emit() methods
- steps should use async functions (async emitters)
- each step should expose a list of events that are emitted and handled

the pipeline should expose a method that creates an SVG showing each step and the events that are connected

when building the pipeline, you need to detect and throw if a step does not subscribe to any event produced by the previous step
