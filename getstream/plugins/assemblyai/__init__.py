"""
AssemblyAI plugin for GetStream.

This plugin provides Speech-to-Text (STT) functionality using AssemblyAI's
real-time streaming API.
"""

from .stt import AssemblyAISTT

__all__ = ["AssemblyAISTT"]
