"""AssemblyAI Speech-to-Text plugin for GetStream.

This module provides real-time speech-to-text transcription using AssemblyAI's
streaming API with WebSocket support.
"""

from .stt import AssemblyAISTT

__all__ = ["AssemblyAISTT"]
