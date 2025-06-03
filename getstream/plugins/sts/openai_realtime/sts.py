"""OpenAI Realtime Speech-to-Speech wrapper that follows the generic STS interface.

This plugin is a thin abstraction around `Call.connect_openai` so that higher-level
examples (or end-users) can treat the AI agent the same way they treat STT/TTS/VAD
plugins.  It:

1. Opens the realtime websocket via the existing SDK helper
2. Applies the initial session presets (instructions, voice, …)
3. Emits every event that flows through so you can subscribe with
   ``on(<event_name>, handler)`` just like the other plugins.

Example
-------

```python
from getstream.stream import Stream
from getstream.plugins.sts.openai_realtime import OpenAIRealtime

client = Stream.from_env()
call = client.video.call("default", "demo-call")
call.get_or_create()

sts_bot = OpenAIRealtime()

# Attach simple logger for every event
@sts_bot.on("*")
async def _(event):
    print("AI event", event)

await sts_bot.connect(call, agent_user_id="assistant")
```
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from getstream.plugins.sts import STS
from getstream.video.call import Call


logger = logging.getLogger(__name__)


class OpenAIRealtime(STS):
    """Speech-to-Speech wrapper for the OpenAI Realtime API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-realtime-preview",
        voice: Optional[str] = None,
        instructions: Optional[str] = None,
    ):
        """Create a new wrapper.

        Args:
            api_key: OpenAI API key. Falls back to ``OPENAI_API_KEY`` env var.
            model: Model ID to use when connecting.
            voice: Optional voice selection passed to the session.
            instructions: Optional system instructions passed to the session.
        """

        super().__init__()

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not provided and not found in env")

        self.model = model
        self.voice = voice
        self.instructions = instructions

        self._connection_cm = None  # type: ignore
        self._connection = None  # type: ignore
        self._listener_task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    async def connect(
        self,
        call: Call,
        agent_user_id: str = "assistant",
        extra_session: Optional[Dict[str, Any]] = None,
    ):
        """Connect an AI agent to *call*.

        Emits:
            • ``connected`` – once the websocket handshake succeeded
            • every event coming from OpenAI/Stream, verbatim
            • ``disconnected`` – after normal closure or error
        """

        if self._is_connected:
            raise RuntimeError("AI agent already connected")

        # 1. Build session presets
        session_payload: Dict[str, Any] = {}
        if self.instructions:
            session_payload["instructions"] = self.instructions
        if self.voice:
            session_payload["voice"] = self.voice
        if extra_session:
            session_payload.update(extra_session)

        # 2. Open connection manager through the SDK helper
        logger.info(
            "Connecting OpenAI agent to call %s/%s using model %s",
            call.call_type,
            call.id,
            self.model,
        )

        self._connection_cm = call.connect_openai(
            self.api_key,
            agent_user_id,
            model=self.model,
        )

        # Enter the async context manually – we want to keep it around and
        # close it ourselves in .close()
        self._connection = await self._connection_cm.__aenter__()

        # Apply session overrides if any
        if session_payload:
            await self._connection.session.update(session=session_payload)

        self._is_connected = True
        self.emit("connected")

        # 3. Start background listener that forwards every event
        self._listener_task = asyncio.create_task(self._listen_events())

    async def close(self):
        """Gracefully close the realtime connection."""

        if not self._is_connected:
            return

        logger.info("Closing OpenAI realtime agent")

        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._connection_cm:
            await self._connection_cm.__aexit__(None, None, None)

        self._is_connected = False
        self.emit("disconnected")

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    async def update_session(self, **session_fields):
        """Wrapper around ``connection.session.update()``."""
        if not self._is_connected or not self._connection:
            raise RuntimeError("Not connected")

        await self._connection.session.update(session=session_fields)

    async def send_user_message(self, text: str):
        """Send a text message from the *human* side to the conversation."""
        if not self._is_connected or not self._connection:
            raise RuntimeError("Not connected")

        await self._connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": text,
                    }
                ],
            }
        )
        await self._connection.response.create()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _listen_events(self):
        """Background task: forward every event to plugin listeners."""

        assert self._connection is not None  # for type checker
        
        logger.info("🔍 Starting event listener task...")

        try:
            logger.info("🔍 Beginning async iteration over OpenAI connection...")
            async for event in self._connection:
                logger.info("🔍 Received event from OpenAI: %s", event.type)
                # Forward verbatim – user can filter by type
                self.emit(event.type, event)
        except Exception as e:
            logger.exception("Error in realtime listener: %s", e)
            self.emit("error", e)
        finally:
            logger.info("🔍 Event listener task ending...")
            # Ensure we mark ourselves disconnected if the server closes first
            if self._is_connected:
                self._is_connected = False
                self.emit("disconnected")


# Re-export for ``from getstream.plugins.sts.openai_realtime import OpenAIRealtime``
__all__ = ["OpenAIRealtime"]