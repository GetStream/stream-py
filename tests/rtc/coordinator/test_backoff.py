"""
Tests for exponential backoff utilities.
"""

import pytest
from getstream.video.rtc.coordinator.backoff import exp_backoff


@pytest.mark.asyncio
async def test_exp_backoff_default_parameters():
    """Test exponential backoff with default parameters (base=1.0, factor=2.0)."""
    max_retries = 5
    expected_delays = [1.0, 2.0, 4.0, 8.0, 16.0]

    actual_delays = []
    async for delay in exp_backoff(max_retries=max_retries):
        actual_delays.append(delay)

    assert actual_delays == expected_delays, (
        f"Expected delays {expected_delays}, but got {actual_delays}"
    )


@pytest.mark.asyncio
async def test_exp_backoff_custom_parameters():
    """Test exponential backoff with custom parameters."""
    max_retries = 3
    base = 0.5
    factor = 3.0
    expected_delays = [0.5, 1.5, 4.5]  # 0.5 * 3^0, 0.5 * 3^1, 0.5 * 3^2

    actual_delays = []
    async for delay in exp_backoff(max_retries=max_retries, base=base, factor=factor):
        actual_delays.append(delay)

    assert actual_delays == expected_delays, (
        f"Expected delays {expected_delays}, but got {actual_delays}"
    )


@pytest.mark.asyncio
async def test_exp_backoff_zero_retries():
    """Test exponential backoff with zero retries."""
    max_retries = 0
    expected_delays = []

    actual_delays = []
    async for delay in exp_backoff(max_retries=max_retries):
        actual_delays.append(delay)

    assert actual_delays == expected_delays, (
        f"Expected no delays for zero retries, but got {actual_delays}"
    )


@pytest.mark.asyncio
async def test_exp_backoff_single_retry():
    """Test exponential backoff with a single retry."""
    max_retries = 1
    base = 2.0
    expected_delays = [2.0]

    actual_delays = []
    async for delay in exp_backoff(max_retries=max_retries, base=base):
        actual_delays.append(delay)

    assert actual_delays == expected_delays, (
        f"Expected delays {expected_delays}, but got {actual_delays}"
    )


@pytest.mark.asyncio
async def test_exp_backoff_fractional_factor():
    """Test exponential backoff with a fractional factor (decreasing delays)."""
    max_retries = 3
    base = 8.0
    factor = 0.5
    expected_delays = [8.0, 4.0, 2.0]  # 8.0 * 0.5^0, 8.0 * 0.5^1, 8.0 * 0.5^2

    actual_delays = []
    async for delay in exp_backoff(max_retries=max_retries, base=base, factor=factor):
        actual_delays.append(delay)

    assert actual_delays == expected_delays, (
        f"Expected delays {expected_delays}, but got {actual_delays}"
    )
