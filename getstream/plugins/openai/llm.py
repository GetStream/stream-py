from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Optional, Sequence, Union

from openai import AsyncOpenAI
from openai.types.responses.response_input_param import ResponseInputParam

from getstream.plugins.common.llm import LLM
from getstream.plugins.common.llm_types import ResponseFormat

OpenAIInput = Union[str, ResponseInputParam]


class OpenAILLM(LLM[OpenAIInput, Dict[str, Any], Dict[str, Any], Any, Any]):
    """Minimal OpenAI Responses adapter.

    Maps `create_response`/`create_response_stream` to `client.responses.create/stream`.
    Text-only mapping for simplicity: concatenates all text parts into a single input string.
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: str = "gpt-4.1-mini",
        client: Optional[AsyncOpenAI] = None,
        **kwargs: Any,
    ) -> None:
        self._client: AsyncOpenAI = client or AsyncOpenAI(api_key=api_key)
        super().__init__(
            provider_name="OpenAI", model=model, client=self._client, **kwargs
        )

    def _collapse_messages(self, messages: Sequence[OpenAIInput]) -> OpenAIInput:
        """Collapse a sequence of OpenAI inputs into a single input.

        Rules (minimal):
        - 0 items: error
        - 1 item: return as-is
        - N>1 all strings: join with newlines
        - Otherwise: return the first item
        """
        if not messages:
            raise ValueError("messages must contain at least one item")
        if len(messages) == 1:
            return messages[0]
        if all(isinstance(m, str) for m in messages):
            return "\n".join(m for m in messages if isinstance(m, str))
        return messages[0]

    async def _create_response_impl(
        self,
        *,
        messages: Sequence[OpenAIInput],
        tools: Optional[Sequence[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
        response_format: Optional[ResponseFormat],
        metadata: Optional[Dict[str, Any]],
    ) -> Any:
        input_value = self._collapse_messages(messages)
        return await self._client.responses.create(
            input=input_value,
            model=self.model,
        )

    async def _create_response_stream_impl(
        self,
        *,
        messages: Sequence[OpenAIInput],
        tools: Optional[Sequence[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
        response_format: Optional[ResponseFormat],
        metadata: Optional[Dict[str, Any]],
    ) -> AsyncIterator[Any]:
        input_value = self._collapse_messages(messages)
        stream_manager = self._client.responses.stream(
            input=input_value,
            model=self.model or "gpt-4.1-mini",
        )

        async def iterator() -> AsyncIterator[Any]:
            async with stream_manager as stream:
                async for event in stream:
                    yield event

        return iterator()

    def _extract_text_delta(self, item: Any) -> Optional[str]:
        # Map common OpenAI stream events to plain text delta for convenience
        ev_type = getattr(item, "type", None)
        if ev_type == "response.output_text.delta":
            delta = getattr(item, "delta", None)
            return delta if isinstance(delta, str) else None
        if ev_type == "response.output_text.done":
            text = getattr(item, "text", None)
            return text if isinstance(text, str) else None
        return None


__all__ = ["OpenAILLM"]
