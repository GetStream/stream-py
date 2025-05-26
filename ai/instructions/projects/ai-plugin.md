# Guide: Adding a New Stream-py Plugin

This document explains the **minimum** you need to know to create a new plugin for the `stream-py` code-base. Follow it step-by-step and you will end up with a **self-contained, tested, and discoverable** plugin.

---

## 1. Where plugins live

```
getstream/plugins/
├── stt/   # speech-to-text plugins
├── tts/   # text-to-speech plugins
└── vad/   # voice activity detection plugins
```

Create a sub-directory named after your plugin inside the correct type folder. Example for a speech-to-text (STT) plugin called `whisper`:

```
getstream/plugins/stt/whisper/
```

Every plugin is an **independent Python package** – it owns its own `pyproject.toml`, dependencies and tests.

---

## 2. Choose the correct base class

| Plugin type                    | Inherit from                |
|--------------------------------|-----------------------------|
| STT (speech-to-text)           | `getstream.plugins.stt.STT` |
| TTS (text-to-speech)           | `getstream.plugins.tts.TTS` |
| VAD (voice activity detection) | `getstream.plugins.vad.VAD` |

Import the base class and implement the abstract methods:

```python
# getstream/plugins/stt/whisper/whisper.py
from getstream.plugins.stt import STT

class Whisper(STT):
    """OpenAI Whisper based STT implementation."""

    name = "whisper"  # mandatory – used for discovery

    def transcribe(self, audio_path: str) -> str:
        # your implementation here
        ...
```

---

## 3. Package skeleton

Inside your plugin folder:

```
whisper/
├── __init__.py          # re-export your class for easy import
├── whisper.py           # main implementation
├── pyproject.toml       # package metadata & deps
└── tests/
    └── test_whisper.py  # unit tests
```

`__init__.py` should expose the plugin class so the registry can import it:

```python
from .whisper import Whisper  # noqa: F401  (re-export for plugin discovery)
```

### Sample `pyproject.toml`

```toml
[project]
name = "getstream-whisper"
version = "0.1.0"
description = "Whisper STT plugin for stream-py"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}

dependencies = [
    "getstream[webrtc]",  # Use webrtc extra for audio/video/WebRTC plugins
    "openai-whisper>=0.1.0",  # replace with your specific runtime deps
]

# Optional: mark this as a plugin for dynamic discovery
[project.entry-points."getstream.plugins.stt"]
whisper = "getstream.plugins.stt.whisper:Whisper"
```

> 📝 **Dependency Note**: Since most plugins work with audio, video, or WebRTC functionality, they should depend on `getstream[webrtc]` rather than just `getstream`. This ensures all necessary WebRTC-related dependencies are available.

---

## 4. Writing tests

1. Put your tests in `whisper/tests/` (or `tests/` inside the plugin folder).
2. **Reuse shared fixtures & helpers** from `getstream.plugins.test_utils`:

```python
# whisper/tests/test_whisper.py
import pytest

from getstream.plugins.test_utils import get_audio_asset
from getstream.plugins.stt.whisper import Whisper

@pytest.fixture()
def plugin():
    return Whisper()


def test_transcribe_simple(plugin):
    audio = get_audio_asset("mia.mp3")
    text = plugin.transcribe(audio)
    assert "hello" in text.lower()
```

Running the test from project root will automatically resolve `test_utils` and load `.env` files thanks to the helper module.

```bash
uv run pytest getstream/plugins/stt/whisper/tests
```

---

## 5. Registering your plugin (optional)

If you rely on dynamic plugin discovery, expose an **entry-point** in `pyproject.toml` (see above). Otherwise, make sure your plugin is imported somewhere in client code so the class is registered.

---

## 6. Providing an example project (highly recommended)

A tiny runnable demo makes it much easier for others to try the plugin.

• Create a separate **Python package** inside the top-level `examples/` folder, e.g.:

```
examples/
└── whisper_demo/
    ├── __init__.py
    ├── main.py          # entry-point that shows how to wire the plugin
    ├── pyproject.toml   # depends on stream-py **and** your plugin package
    └── README.md        # how to run the demo
```

• The example's `pyproject.toml` should list your plugin in its dependencies so a simple `uv pip install -e .` inside the example folder pulls everything needed.

• Keep the demo minimal: a short script that loads some sample data (use assets from `tests/assets` if possible), runs the plugin, and prints or plays the result.

• **Optimize for readability**: The `main.py` file should be clean and easy to follow. Keep the main function focused on the core logic flow. Move error handling (try/except blocks) to the entry point (`if __name__ == "__main__":`) rather than cluttering the main function. This makes it easier for users to understand the essential steps and adapt the code to their needs.

• Examples are **optional but strongly encouraged**; they double as integration smoke-tests and real-world documentation.

---

## 7. Checklist before opening a PR

- [ ] Sub-directory under the correct plugin type.
- [ ] Inherits from the right base class.
- [ ] Contains `pyproject.toml` with precise dependencies.
- [ ] Includes at least one passing test that uses `getstream.plugins.test_utils`.
- [ ] Exports the plugin class in `__init__.py`.
- [ ] (Recommended) Adds a minimal example project under `examples/` that demonstrates basic usage.
- [ ] `uv run pytest` passes from project root.

Happy hacking! 🎉
