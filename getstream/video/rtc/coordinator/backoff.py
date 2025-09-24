"""
Exponential backoff implementation for WebSocket reconnection.

This module provides utilities for implementing exponential backoff strategies
when reconnecting to failed WebSocket connections.
"""

import logging
from typing import AsyncIterator

logger = logging.getLogger(__name__)


async def exp_backoff(
    max_retries: int, base: float = 1.0, factor: float = 2.0
) -> AsyncIterator[float]:
    """
    Generate exponential backoff delays for retry attempts.

    Args:
        max_retries: Maximum number of retry attempts
        base: Base delay in seconds for the first retry
        factor: Multiplicative factor for each subsequent retry

    Yields:
        float: Delay in seconds for each retry attempt

    Example:
        >>> import asyncio
        >>> async def example():
        ...     delays = []
        ...     async for delay in exp_backoff(max_retries=3, base=1.0, factor=2.0):
        ...         delays.append(delay)
        ...     return delays
        >>> delays = asyncio.run(example())
        >>> delays
        [1.0, 2.0, 4.0]
    """
    for attempt in range(max_retries):
        delay = base * (factor**attempt)
        logger.debug(f"Backoff attempt {attempt + 1}/{max_retries}: {delay}s delay")
        yield delay
