
Read file: getstream/plugins/stt/deepgram/tests/test_stt.py

“Refactor Deepgram STT for real-time transcript emission”

Please modify the following files only:

1. getstream/plugins/stt/deepgram/stt.py
2. (optional but preferred) getstream/plugins/stt/__init__.py – add a tiny helper if you decide to share background-dispatch logic across providers.

Required behaviour

A. Background dispatcher
   • In Deepgram._setup_connection() create an asyncio task (e.g. self._result_task) that runs a private async method _result_dispatch_loop().
   • The loop must do `item = await self._results_queue.get()` and, for every item:
     – if item is (is_final, text, metadata): emit `"transcript"` when is_final else `"partial_transcript"`;
     – if item is an Exception (our error sentinel) emit `"error"`.
   • The loop exits cleanly when self._running becomes False.
   • Store the task so it can be cancelled in close().

B. Thread-safety for callbacks
   • handle_transcript / handle_error in _setup_connection must push into the queue using `asyncio.get_running_loop().call_soon_threadsafe(...)` because the Deepgram SDK may call the handlers on a different thread.

C. Slimmer _process_audio_impl
   • Keep the existing audio-sending logic (conversion + `self.dg_connection.send(...)`).
   • REMOVE the section that drains self._results_queue – result delivery is now the dispatch loop’s job.
   • Return None; callers no longer need the results list.

D. Lifecycle
   • In close():
       – cancel self._result_task, await it and ignore CancelledError.
       – keep the rest of the cleanup.
   • Guard double-initialisation / double-close.

E. Do **not** break Silero VAD, TTS, or existing public APIs. No new dependencies.

F. Logging
   • Add concise INFO logs when the dispatcher starts/stops and DEBUG logs for each item processed.

------------------------------------------------
PROMPT #2 – Update / add tests
Title: “Tests for immediate transcript emission”

Files to touch / create:

1. tests/plugins/stt/deepgram/test_stt.py   (update existing)
2. tests/plugins/stt/deepgram/test_realtime.py   (new)

Changes & expectations

A. Adjust existing unit-tests
   • All tests that pushed items into `stt._results_queue` and then called `await stt.process_audio(...)` must now *await a small sleep* (e.g. 0.05 s) to let the background dispatcher emit events.
   • Remove calls that rely on `_process_audio_impl` draining the queue – that code path no longer exists.

B. New real-time test (test_realtime.py)
   Purpose: guarantee that a transcript is emitted without having to send a second chunk of audio.

   Steps:
   1. Use the existing MockDeepgramClient / MockDeepgramConnection.
   2. Instantiate Deepgram(), register a transcript event collector list.
   3. Simulate audio:
        pcm = PcmData(samples=b"\x00\x00"*800, sample_rate=48000, format="s16")
        await stt.process_audio(pcm)        # send some bytes
        # immediately trigger server transcript
        stt.dg_connection.emit_transcript("hello world")
   4. Await asyncio.sleep(0.05).
   5. Assert len(collected) == 1 and collected[0][0] == "hello world".
   6. Cleanup.

C. Continuous-integration speed
   • Keep sleeps short (≤0.1 s).
   • Mark tests that hit the real server unchanged but ensure they still pass.

D. No network access is necessary for the new test; rely on mocks only.

E. When finished, run tests for all changed files using uv pytest and from the root project
