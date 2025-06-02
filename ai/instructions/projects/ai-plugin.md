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

## 3. Shared audio utilities

For common audio processing tasks, use the shared utilities in `getstream.audio.utils`:

```python
from getstream.audio.utils import resample_audio

# High-quality resampling with automatic fallbacks
resampled_audio = resample_audio(audio_data, from_sample_rate, to_sample_rate)
```

**Available utilities:**
- `resample_audio(frame, from_sr, to_sr)` – Multi-backend resampler that prefers scipy.signal.resample_poly, falls back to torchaudio, and has a simple averaging fallback for tests

This avoids duplicating resampling logic across plugins and ensures consistent, high-quality audio processing.

---

## 4. Package skeleton

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

# Required for UV workspace
[tool.uv.sources]
getstream = { workspace = true }
getstream-plugins-stt-deepgram = { workspace = true }
getstream-plugins-tts-elevenlabs = { workspace = true }
getstream-plugins-vad-silero = { workspace = true }
```

> 📝 **Dependency Note**: Since most plugins work with audio, video, or WebRTC functionality, they should depend on `getstream[webrtc]` rather than just `getstream`. This ensures all necessary WebRTC-related dependencies are available. The `[tool.uv.sources]` section is required for the workspace setup to use the local development version of getstream.

---

## 5. Writing tests

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

## 6. Registering your plugin (optional)

If you rely on dynamic plugin discovery, expose an **entry-point** in `pyproject.toml` (see above). Otherwise, make sure your plugin is imported somewhere in client code so the class is registered.

---

## 7. Providing an example project (highly recommended)

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

**Example dependencies:**
```toml
dependencies = [
    "getstream[webrtc]",
    "getstream-plugins-stt-whisper",  # Use the plugin package, not openai-whisper directly
    "python-dotenv>=1.0.0",
]
```

This approach ensures that:
- The example uses the exact plugin implementation you built
- All plugin dependencies are automatically included
- The example works with the workspace development setup

• Keep the demo minimal: a short script that loads some sample data (use assets from `tests/assets` if possible), runs the plugin, and prints or plays the result.

• **Optimize for readability**: The `main.py` file should be clean and easy to follow. Keep the main function focused on the core logic flow. Move error handling (try/except blocks) to the entry point (`if __name__ == "__main__":`) rather than cluttering the main function. This makes it easier for users to understand the essential steps and adapt the code to their needs.

• Examples are **optional but strongly encouraged**; they double as integration smoke-tests and real-world documentation.

---

## 8. Checklist before opening a PR

- [ ] Sub-directory under the correct plugin type.
- [ ] Inherits from the right base class.
- [ ] Contains `pyproject.toml` with precise dependencies.
- [ ] Includes at least one passing test that uses `getstream.plugins.test_utils`.
- [ ] Exports the plugin class in `__init__.py`.
- [ ] (Recommended) Adds a minimal example project under `examples/` that demonstrates basic usage.
- [ ] `uv run pytest` passes from project root.

---

## 9. Working with the UV Workspace

This project uses UV workspace configuration for seamless local development across plugins, the main package, and examples.

### Workspace Setup

The root `pyproject.toml` defines a workspace that includes:
- All plugins: `getstream/plugins/stt/*`, `getstream/plugins/tts/*`, `getstream/plugins/vad/*`
- All examples: `examples/*`
- The main `getstream` package (root)

### Development Workflow

**Initial setup:**
```bash
# From project root - installs everything in editable mode
uv sync --dev --all-extras --all-packages
```

**Adding a new plugin to the workspace:**
New plugins and examples are automatically included! The workspace uses wildcard patterns:
```toml
[tool.uv.workspace]
members = [
    "getstream/plugins/*/*",        # Automatically includes all plugins
]
exclude = [
    "**/__pycache__",              # Exclude cache directories
]
```

Just create your plugin or example with a `pyproject.toml` file in the right location and it will be automatically included.

**Plugin development:**
```bash
# All packages are automatically available in editable mode
# Changes to getstream core are immediately available to plugins
# Changes to plugins are immediately available to examples

# Run tests for a specific plugin
uv run pytest getstream/plugins/stt/whisper/tests/ -v

# Run tests for all plugins
uv run pytest getstream/plugins/ -v

# Run example
cd examples/your_example_name
uv run python main.py
```

**Key Benefits:**
- ✅ **No manual editable installs**: Everything is automatically linked
- ✅ **Immediate changes**: Modifications to any package are instantly available
- ✅ **Consistent dependencies**: Single lock file manages all versions
- ✅ **Easy testing**: Run tests across the entire workspace
- ✅ **Simple CI**: Single command to test everything

### Plugin Dependencies

In your plugin's `pyproject.toml`, you can simply depend on `getstream[webrtc]` - the workspace ensures it uses the local development version. You should also include workspace sources for all plugins to enable cross-plugin dependencies:

```toml
dependencies = [
    "getstream[webrtc]",  # Uses local workspace version during development
    "your-plugin-specific-deps>=1.0.0",
]

[tool.uv.sources]
getstream = { workspace = true }
getstream-plugins-stt-deepgram = { workspace = true }
getstream-plugins-tts-elevenlabs = { workspace = true }
getstream-plugins-vad-silero = { workspace = true }
# Add any new plugins here as they're created
```

### Publishing vs Development

- **Development**: Workspace automatically uses local versions
- **Publishing**: When published to PyPI, plugins will use the published `getstream[webrtc]` package

This gives you the best of both worlds: easy local development with proper published dependencies.

---

## 10. Checklist before opening a PR

- [ ] Sub-directory under the correct plugin type.
- [ ] Inherits from the right base class.
- [ ] Contains `pyproject.toml` with precise dependencies.
- [ ] Includes at least one passing test that uses `getstream.plugins.test_utils`.
- [ ] Exports the plugin class in `__init__.py`.
- [ ] (Recommended) Adds a minimal example project under `examples/` that demonstrates basic usage.
- [ ] `uv run pytest` passes from project root.
- [ ] When adding external dependencies, make sure to specify conservative version constraints (eg. dont use >=2.4.0)
