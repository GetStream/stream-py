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
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from benchmarks._support import (
    NETEM_PROFILES,
    LoadGuardError,
    check_load_guard,
    collect_metadata,
    has_stream_credentials,
)

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
        "--resource-only",
        action="store_true",
        help="Run only isolated CPU/RSS soaks (audio + 720p video) in this process",
    )
    parser.add_argument(
        "--resource-inline",
        action="store_true",
        help=(
            "Run CPU/RSS soaks in the same process as join/e2e (not comparable; "
            "debug only). Default is a fresh child process."
        ),
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
        default=30,
        help="Repeated runs for join / e2e-audio live benches (default: 30)",
    )
    parser.add_argument(
        "--soak-seconds",
        type=float,
        default=60.0,
        help="Duration of the live publish+subscribe soak (default: 60)",
    )
    parser.add_argument(
        "--soak-repeats",
        type=int,
        default=3,
        help="Isolated CPU/RSS soak repeats per kind (default: 3)",
    )
    parser.add_argument(
        "--reconnect-runs",
        type=int,
        default=15,
        help="Repeated runs for reconnect recovery (default: 15)",
    )
    parser.add_argument(
        "--profile",
        choices=NETEM_PROFILES,
        default="clean",
        help=(
            "Netem impairment profile recorded in metadata. Apply on Linux with "
            "sudo benchmarks/netem/apply.sh <profile> (default: clean)"
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args(argv)


_LIVE_SKIP_NAMES = (
    "live.join_latency_ms",
    "live.join_token_mint_ms",
    "live.join_coordinator_rest_ms",
    "live.join_rtc_session_ms",
    "live.audio_e2e_latency_ms",
    "live.soak_cpu_percent",
    "live.soak_rss_import_mb",
    "live.soak_rss_baseline_mb",
    "live.soak_rss_steady_median_mb",
    "live.soak_rss_peak_mb",
    "live.soak_rss_maxrss_mb",
    "live.soak_rss_growth_slope_mb_per_s",
    "live.soak_nthreads_median",
    "live.video_soak_cpu_percent",
    "live.video_soak_rss_import_mb",
    "live.video_soak_rss_baseline_mb",
    "live.video_soak_rss_steady_median_mb",
    "live.video_soak_rss_peak_mb",
    "live.video_soak_rss_maxrss_mb",
    "live.video_soak_rss_growth_slope_mb_per_s",
    "live.video_soak_nthreads_median",
    "live.reconnect_recovery_ms",
    "live.video_publish_720p30_bytes_sent",
    "live.video_publish_720p30_packets_sent",
    "live.dtx_silence_bytes_sent",
    "live.dtx_speech_bytes_sent",
)


def _merge_resource_child(args: argparse.Namespace) -> dict[str, Any]:
    fd, tmp_name = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    tmp = Path(tmp_name)
    cmd = [
        sys.executable,
        "-m",
        "benchmarks.run",
        "--resource-only",
        "--output",
        str(tmp),
        "--soak-seconds",
        str(args.soak_seconds),
        "--soak-repeats",
        str(args.soak_repeats),
        "--profile",
        args.profile,
    ]
    if args.verbose:
        cmd.append("-v")
    logger.info("Running isolated resource soaks in a child process")
    env = os.environ.copy()
    env["STREAM_BENCH_RESOURCE_CHILD"] = "1"
    completed = subprocess.run(cmd, env=env)
    if not tmp.exists() or tmp.stat().st_size == 0:
        return {
            "benchmarks": [],
            "skipped": [],
            "errors": [
                {
                    "name": "live.soak_cpu_percent",
                    "reason": f"resource child exited {completed.returncode} with no JSON",
                }
            ],
        }
    payload = json.loads(tmp.read_text())
    tmp.unlink(missing_ok=True)
    if completed.returncode != 0 and not payload.get("errors"):
        payload.setdefault("errors", []).append(
            {
                "name": "live.soak_cpu_percent",
                "reason": f"resource child exited {completed.returncode}",
            }
        )
    return payload


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    benchmarks: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    if args.resource_only:
        if has_stream_credentials():
            from benchmarks.benches.live import run_resource_benches

            logger.info("Running isolated CPU/RSS soaks")
            res, skip, err = await run_resource_benches(
                soak_seconds=args.soak_seconds,
                soak_repeats=args.soak_repeats,
            )
            benchmarks.extend(res)
            skipped.extend(skip)
            errors.extend(err)
        else:
            reason = "STREAM_API_KEY / STREAM_API_SECRET not set"
            for name in _LIVE_SKIP_NAMES:
                if "soak" in name:
                    skipped.append({"name": name, "reason": reason})
        return {
            "metadata": collect_metadata(netem_profile=args.profile),
            "benchmarks": benchmarks,
            "skipped": skipped,
            "errors": errors,
        }

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
            from benchmarks.benches.live import run_live_benches, run_resource_benches

            logger.info("Running live SFU benches")
            live_results, live_skipped, live_errors = await run_live_benches(
                runs=args.live_runs,
                reconnect_runs=args.reconnect_runs,
            )
            benchmarks.extend(live_results)
            skipped.extend(live_skipped)
            errors.extend(live_errors)
            if args.resource_inline or os.environ.get("STREAM_BENCH_RESOURCE_CHILD"):
                logger.warning("CPU/RSS soaks running in-process; numbers are not isolated")
                res, skip, err = await run_resource_benches(
                    soak_seconds=args.soak_seconds,
                    soak_repeats=args.soak_repeats,
                )
                benchmarks.extend(res)
                skipped.extend(skip)
                errors.extend(err)
            else:
                child = _merge_resource_child(args)
                benchmarks.extend(child.get("benchmarks") or [])
                skipped.extend(child.get("skipped") or [])
                errors.extend(child.get("errors") or [])
        else:
            reason = "STREAM_API_KEY / STREAM_API_SECRET not set"
            logger.warning("Skipping live SFU benches: %s", reason)
            for name in _LIVE_SKIP_NAMES:
                skipped.append({"name": name, "reason": reason})

    return {
        "metadata": collect_metadata(netem_profile=args.profile),
        "benchmarks": benchmarks,
        "skipped": skipped,
        "errors": errors,
    }

    return {
        "metadata": collect_metadata(netem_profile=args.profile),
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
    if args.resource_only and args.local_only:
        logger.error("Choose at most one of --resource-only / --local-only")
        return 2

    try:
        check_load_guard()
    except LoadGuardError as exc:
        logger.error("%s", exc)
        return 3

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
