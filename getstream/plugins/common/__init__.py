"""Common abstract base classes and utilities shared by all Stream AI plugins.

Moving forward, provider wheels (`stream-plugins-deepgram`, …) should depend on
this package for the canonical definitions of STT, TTS, VAD, …
"""

from .stt import STT  # noqa: F401
from .tts import TTS  # noqa: F401
from .sts import STS  # noqa: F401
from .vad import VAD  # noqa: F401

__all__ = [
    "STT",
    "TTS",
    "STS",
    "VAD",
]
