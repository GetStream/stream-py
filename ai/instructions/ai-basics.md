## Project setup

1. This project uses `uv`,  `pyproject.toml` and venv to manage dependencies
2. Never use pip directly, use `uv add` to add dependencies and `uv sync --dev --all-packages` to install the dependency
3. Do not change code generated python code, `./generate.sh` is the script responsible of rebuilding all API endpoints and API models
4. **WebRTC Dependencies**: All dependencies related to WebRTC, audio, video processing (like `aiortc`, `numpy`, `torch`, `torchaudio`, `soundfile`, `scipy`, `deepgram-sdk`, `elevenlabs`, etc.) are organized under the `webrtc` optional dependencies group. Plugins that work with audio, video, or WebRTC functionality should depend on `getstream[webrtc]` instead of just `getstream`.

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
