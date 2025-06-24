# GetStream TEN Plugin

A plugin for GetStream that provides TEN (Text-to-Everything) functionality.

## Installation

This plugin is part of the GetStream workspace and can be installed with:

```bash
uv sync --all-packages --all-extras
```

## Usage

```python
from getstream.plugins.ten import vad, turn

# Use the VAD (Voice Activity Detection) functionality
# Use the TURN (Text-to-URN) functionality
```

## Dependencies

- getstream[webrtc]
- transformers>=4.0.0 l