───────────────────────────────
STAGE 1 — Clean-up the base VAD
───────────────────────────────

Make the generic `VAD` class safe for streaming and testable in isolation.

Code changes
1. `getstream/plugins/vad/__init__.py`
   a. Add `self._leftover: np.ndarray = np.empty(0, np.int16)`
   b. In `process_audio()`
      • prepend `self._leftover` to the new samples;
      • process only full frames (`while len(buffer) >= frame_size`) – **no zero-padding**;
      • keep the tail in `self._leftover`.
   c. Convert all length thresholds (`speech_pad_*`, `min_speech_*`, …) to milliseconds and compute required frame counts on the fly so later changes to `frame_size` stay valid.
   d. Public `async def flush(self):` wrapper that calls the (renamed) `_flush_speech_buffer`.
2. Keep current logging style but switch “missing samples” from `logger.debug` to `logger.warning` to catch edge cases faster.

Tests
• Update existing Silero tests so they call `await vad.flush()` instead of the private method.
• Add `test_silence_no_turns`: feed 5 s of zeros, assert that no `audio` event fires.
`verify_detected_speech()` tolerance stays at ±55 % for now (we will tighten later).

Pass criteria
All tests green, no Ruff violations, and CPU time unchanged (<±3 %).

────────────────────────────────────────────
STAGE 2 — Model-aware chunking & resampling
────────────────────────────────────────────
Goal
Guarantee that whatever sample-rate arrives, the Silero model always receives 16 kHz, 512|1024|1536 sample windows.

Code changes
1. `getstream/plugins/vad/silero/vad.py`
   a. New ctor args:
      `model_rate=16000`, `window_samples=1536`, `device="cpu"`.
   b. Replace `_resample_audio()` with a band-limited polyphase helper:
      ```python
      def _resample(frame, from_sr, to_sr):
          if from_sr == to_sr:
              return frame
          return scipy.signal.resample_poly(frame, to_sr, from_sr, axis=-1)
      ```
      (fall back to torchaudio if available).
   c. Persistent hidden state:
      ```
      self.h, self.c = None, None
      prob, self.h, self.c = self.model(tensor, self.h, self.c, model_sr)
      ```
      Reset them in `reset()` and right after emitting a turn.
   d. Keep a raw-sample bytearray (`self._raw_buffer`) in **input** sample-rate and only resample slices that form a complete window.
   e. Remove the “min_buffer_samples” magic; instead wait until `len(self._resampled) >= window_samples`.
2. Update `__init__.py` thresholds to default to Silero: `frame_size` → `window_samples` (1536 @ 16 kHz ≈ 96 ms).

Tests
• Add asset `speech_48k.wav` (<256 KB).
• New `test_mixed_samplerate` – feed that 48 kHz clip, expect the same single turn length as for 16 kHz copy.
• Existing tests still pass.

Pass criteria
All tests green; `rtf = processing_time / audio_time` reported by `logger.debug` ≤ 0.2 on CPU.

──────────────────────────────────────────────
STAGE 3 — Proper turn-detection state machine
──────────────────────────────────────────────
Goal
Match fastrtc’s behaviour: asymmetric thresholds, early partial events, efficient buffers.

Code changes
1. Base `VAD` (same file):
   a. Accept new ctor params: `activation_th=0.5`, `deactivation_th=0.35`.
   b. Replace the old `silence_counter / speech_counter` logic by:
      ```
      if prob >= activation_th:   # start/keep speech
      if prob < deactivation_th:  # start/keep silence
      ```
      This removes the need for two separate counters.
   c. Every N windows (e.g. 10) while in speech emit
      `self.emit("partial", pcm_chunk, user)` so downstream UI can show live wave-form.
   d. Replace list-of-numpy `speech_buffer` by `bytearray` to avoid O(n²) mem-copy.

2. Silero subclass: no code change – it already feeds probabilities upstream.

Tests
• Tighten duration tolerance to ±10 % and add “expected number of turns = 1”.
• New `test_streaming_chunks_20ms` (kept from original suite) now **must** match the single-turn detection test exactly.
• Verify that at least one `partial` event was observed before each final `audio`.

Pass criteria
Tests green with stricter asserts; `bytearray` profiling shows ≤ 1 copy per 1 MB of speech (rough check with `tracemalloc`).

────────────────────────────────────────────
STAGE 4 — Polish, performance, configurability
────────────────────────────────────────────
Goal
Give production-ready touches and optional optimisations.

Code changes
1. Silero VAD
   • Allow `device="cuda:0"`; fall back to CPU if not available.
   • Optional `use_onnx=True` switches to ORT session (load once, call `run(None, {input_name: arr})`).
   • Deprecation warning if user passes `frame_size` instead of `window_samples`.
2. Logging
   • At INFO: `logger.info("Turn emitted", extra={"duration_ms": dur, "samples": n})`
   • At DEBUG: each window logs `{"p": prob, "rtf": rtf}` (already in Stage 2).
3. Docs
   • Update module docstrings and README snippet.
4. Lint & format (`ruff format getstream/ tests/`).

Tests
• Add `test_cuda_fallback` (mark xfail if CUDA not present).
• Add `test_flush_api` – stream half a sentence, call `flush()`, ensure turn is emitted.
• Run `pytest -q` plus `uv run python -m timeit -n5 -s "from tests.bench import bench"` (simple 10-s benchmark).

Pass criteria
All tests (incl. CPU fallback path) pass; benchmark shows **no** regression vs Stage 3; Ruff clean.

───────────────────────────────
After Stage 4 the upgraded VAD ships the same ergonomic contract as fastrtc’s implementation, handles any PCM rate, streams efficiently, exposes partial events and is fully covered by deterministic tests.
