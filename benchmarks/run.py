"""Run the backend-agnostic RTC benchmark harness.

Writes a JSON document with environment metadata and per-bench samples so the
same suite can be re-run against a later RTC backend.

Usage::

    uv run python -m benchmarks.run --output benchmarks/results/aiortc-baseline.json
    uv run python -m benchmarks.run --local-only
    uv run python -m benchmarks.compare baseline.json candidate.json

Live SFU benches skip cleanly when STREAM_API_KEY / STREAM_API_SECRET are unset.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from benchmarks._support import collect_metadata, has_stream_credentials

logger = logging.getLogger("benchmarks")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks/results/latest.json"),
        help="Path to write JSON results (default: benchmarks/results/latest.json)",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Run only local microbenchmarks",
    )
    parser.add_argument(
        "--live-only",
        action="store_true",
        help="Run only live SFU benches (still skip if credentials are missing)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=7,
        help="Timed iterations for local microbenchmarks (default: 7)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=2,
        help="Warmup iterations for local microbenchmarks (default: 2)",
    )
    parser.add_argument(
        "--live-runs",
        type=int,
        default=5,
        help="Repeated runs for join / e2e-audio live benches (default: 5)",
    )
    parser.add_argument(
        "--soak-seconds",
        type=float,
        default=60.0,
        help="Duration of the live publish+subscribe soak (default: 60)",
    )
    parser.add_argument(
        "--reconnect-runs",
        type=int,
        default=3,
        help="Repeated runs for reconnect recovery (default: 3)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    benchmarks: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    if not args.live_only:
        from benchmarks.benches.local import run_local_benches

        logger.info("Running local microbenchmarks")
        local_results, local_errors = await run_local_benches(
            iterations=args.iterations,
            warmup=args.warmup,
        )
        benchmarks.extend(local_results)
        errors.extend(local_errors)

    if not args.local_only:
        if has_stream_credentials():
            from benchmarks.benches.live import run_live_benches

            logger.info("Running live SFU benches")
            live_results, live_skipped, live_errors = await run_live_benches(
                runs=args.live_runs,
                soak_seconds=args.soak_seconds,
                reconnect_runs=args.reconnect_runs,
            )
            benchmarks.extend(live_results)
            skipped.extend(live_skipped)
            errors.extend(live_errors)
        else:
            reason = "STREAM_API_KEY / STREAM_API_SECRET not set"
            logger.warning("Skipping live SFU benches: %s", reason)
            for name in (
                "live.join_latency_ms",
                "live.audio_e2e_latency_ms",
                "live.soak_cpu_percent",
                "live.soak_rss_mb",
                "live.reconnect_recovery_ms",
            ):
                skipped.append({"name": name, "reason": reason})

    return {
        "metadata": collect_metadata(),
        "benchmarks": benchmarks,
        "skipped": skipped,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if args.local_only and args.live_only:
        logger.error("Choose at most one of --local-only / --live-only")
        return 2

    payload = asyncio.run(_run(args))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    logger.info("Wrote %s", args.output)

    n_ok = len(payload["benchmarks"])
    n_skip = len(payload["skipped"])
    n_err = len(payload["errors"])
    logger.info("Finished: %d benches, %d skipped, %d errors", n_ok, n_skip, n_err)
    for item in payload["skipped"]:
        logger.info("  skipped %s (%s)", item["name"], item["reason"])
    for item in payload["errors"]:
        logger.error("  error %s: %s", item["name"], item["reason"])
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
