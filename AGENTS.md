## Project setup

1. This project uses `uv`,  `pyproject.toml` and venv to manage dependencies
2. Never use pip directly, use `uv add` to add dependencies and `uv sync --dev --all-packages --all-extras` to install the dependency (without `--all-extras` the sync removes the packages of the optional dependency groups, for example `aiortc`, `av` and `numpy`)
3. Do not change code generated python code, `./generate.sh` is the script responsible of rebuilding all API endpoints and API models
4. **WebRTC Dependencies**: The dependencies of `getstream.video.rtc` (`getstream-rtc`, `aiortc`, `av`, `numpy`, and `twirp`, `protobuf` and `aiohttp` for the generated SFU code) are organized under the `webrtc` optional dependencies group. Plugins that work with audio, video, or WebRTC functionality should depend on `getstream[webrtc]` instead of just `getstream`, and declare every other package they import themselves.
5. **Rust bindings**: `getstream-rtc` (directory `getstream-rtc/`) is a separate distribution and a member of the uv workspace. Its package `getstream_rtc` contains the PyO3 extension `getstream_rtc._bindings`, which maturin builds from `getstream-rtc/Cargo.toml` (sources in `getstream-rtc/rustsrc/`), and exports every class at its root. It wraps the Rust SDK (`getstream` crate from https://github.com/GetStream/stream-video-rust). It does not depend on `getstream`; stream-py code imports `getstream_rtc` as a separate package, and only the `webrtc` extra installs it. Its version is independent of the `getstream` version and is only in `getstream-rtc/pyproject.toml` (the crate has no version). `uv sync` compiles it when it installs the `webrtc` extra or all workspace packages; this needs the Rust toolchain pinned in `getstream-rtc/rust-toolchain.toml`, a C compiler, `cmake`, `pkg-config`, `libvpx`, and libclang for bindgen (macOS: `brew install libvpx cmake pkg-config`, libclang comes with Xcode; Debian/Ubuntu: `apt install libvpx-dev libclang-dev cmake pkg-config build-essential`). After Rust changes, run `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings` and `cargo test --lib` in `getstream-rtc/`; rustup selects the toolchain from the current directory, not from `--manifest-path`.

## Python testing

1. pytest is used for testing
2. use `uv run pytest` to run tests
3. pytest preferences are stored in pytest.ini
4. fixtures are used to inject objects in tests
5. test using the Stream API client can use the fixture
6. .env is used to load credentials, the client fixture will load credentials from there
7. keep tests well organized and use test classes for similar tests
8. tests that rely on file assets should always rely on files inside the `tests/assets/` folder, new files should be added there and existing ones used if possible. Do not use files larger than 256 kilobytes.
9. do not use mocks or mock things in general unless you are asked to do that directly
10. always run tests using `uv run pytest` from the root of the project, dont cd into folders to run tests


## Rust and async expectations

- Ensure [rust-skills](https://github.com/leonardomso/rust-skills) is available
  before coding or review. Install or refresh it with
  `npx add-skill leonardomso/rust-skills`, then apply the relevant rules rather
  than loading unrelated categories.
- Prefer typed errors and `Result`; avoid panics and `unwrap` in library code.
- Do not circumvent borrow checker with .clone() for no reason.
- Keep queues and buffers bounded. Make background-task cancellation and cleanup
  deterministic, and do not hold synchronous locks across `.await` points.
- Preserve compatibility with the Rust version declared in
  `getstream-rtc/Cargo.toml`.

## Rust wrapper: GIL, locks and deadlocks

Python threads, tokio worker threads and the logging forwarding thread all use
SDK locks (`std::sync::Mutex`, tokio locks and channels) and the GIL. A deadlock
needs a thread that holds an SDK lock and waits for the GIL while another thread
holds the GIL and waits for that lock. Before you add or change a binding, read
the SDK functions it calls and find the locks they take. Keep both halves
impossible:

- A Python thread must not hold the GIL while it waits for an SDK lock. Release
  the GIL with `py.detach` in every synchronous method that reads or changes SDK
  state (for example `Call.participants()`, `LocalAudioTrack.flush()`). A method
  whose locks no other thread can hold yet needs no `py.detach` (`Client.call`
  creates the call it locks).
- A thread that holds an SDK lock must never wait for the GIL. Callbacks given
  to the SDK (for example `on_track`) must not call `Python::attach` or drop
  Python objects; they hand data over through a bounded channel.
- `future_into_py` futures run on tokio without the GIL. Do not call
  `Python::attach` in them; return the value and let pyo3-async-runtimes convert
  it.
- Never call Python from a `tracing` layer or a `log` logger. Records go through
  the bounded queue in `getstream-rtc/rustsrc/logging.rs`; only its forwarding
  thread, which holds no SDK lock, takes the GIL.
- Python destructors drop the SDK objects they own with the GIL held. When you
  update the SDK, check that these drops (`Call`, `RemoteTrack`,
  `VideoFrameStream`, local tracks, tracks in the track queue) still take no
  lock that another thread can hold.
- While the GIL is released, do not read memory that Python owns (for example a
  numpy buffer); copy it first.

### Calling Python from Rust

- Do not call Python code from Rust (`py.import(...)`, `call_method`, `call1`,
  `getattr` of a Python object) unless the user agreed to it first. It makes the
  code more complex and slower, so it is always a developer decision.
- Return values that PyO3 converts by itself (`bool`, integers, `f64`, `String`,
  `Vec`, `Option`, pyclasses) and let the Python caller convert them further,
  for example a Unix time in seconds to a `datetime`.

### Logging in the wrapper

- Log with the `tracing` macros (`tracing::debug!` and the others). Do not use
  `println!`, the `log` macros, or Python `logging` through `Python::attach`.
- Use the default target. Records of the wrapper (`_bindings::…`) and of the SDK
  (`getstream::…`) use the `level` of `configure_logging`; records of other
  crates use `third_party_level`. A record reaches the configured logger's
  child, for example `getstream._bindings.call` for
  `getstream-rtc/rustsrc/call.rs` and `getstream.rtc.join` for the SDK's
  `getstream::rtc::join`.
- The message is an event name in the SDK style, `stream.<area>.<event>`. Put
  values in fields, not in the message:
  `tracing::debug!(dropped_samples = n, "stream.rtc.audio.pcm_queue_overflow")`.
- Each field becomes an attribute of the Python `LogRecord`. Dots in field names
  become `_`, a name that `LogRecord` already has gets the prefix `rust_`, and
  `rust_target` holds the Rust target. Booleans, integers, floats and strings
  keep their type; other values become strings (`?value` for `Debug`, `%value`
  for `Display`). An error field includes its source chain.
- Levels map to Python as ERROR 40, WARN 30, INFO 20, DEBUG 10, TRACE 5.
- A log call never blocks and never takes the GIL, so it is safe while a lock or
  the GIL is held. When the queue (1024 records) is full, records are dropped and
  counted; a `stream.rust.log_records_dropped` warning with `dropped` comes before the
  next delivered record.
- Nothing is forwarded until `configure_logging` sets a logger. Disabled records
  are filtered before their fields are formatted.
- Never log secrets or tokens.
- To assert on records in tests, including DEBUG ones, use the `sdk_logs`
  fixture in `getstream-rtc/tests/conftest.py`, and call
  `getstream_rtc.configure_logging(None, logging.NOTSET)` before you assert: it
  returns after the queued records are delivered.
