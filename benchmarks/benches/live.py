"""Live SFU benches (filled in a follow-up commit)."""

from __future__ import annotations

from typing import Any


async def run_live_benches(
    *, runs: int, soak_seconds: float, reconnect_runs: int
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    return [], [], []
