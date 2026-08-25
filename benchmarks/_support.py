"""Shared helpers for the RTC benchmark harness."""

from __future__ import annotations

import os
import platform
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable, Optional

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = REPO_ROOT / "tests" / "assets"

SPEECH_16K = ASSETS_DIR / "formant_speech_16k.wav"
SPEECH_48K = ASSETS_DIR / "formant_speech_48k.wav"
TONE_16K = ASSETS_DIR / "speech_tone.wav"


def load_env() -> None:
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv()


def has_stream_credentials() -> bool:
    load_env()
    return bool(os.environ.get("STREAM_API_KEY") and os.environ.get("STREAM_API_SECRET"))


def detect_backend() -> str:
    override = os.environ.get("STREAM_RTC_BACKEND")
    if override:
        return override
    try:
        import getstream_rtc_core  # noqa: F401
    except ImportError:
        return "aiortc"
    return "rust"


def _package_version(name: str) -> Optional[str]:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _cpu_model() -> str:
    if sys.platform == "darwin":
        try:
            brand = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if brand:
                return brand
        except (OSError, subprocess.CalledProcessError):
            pass
    return platform.processor() or platform.machine()


def _git_sha() -> Optional[str]:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def collect_metadata() -> dict[str, Any]:
    versions = {
        "getstream": _package_version("getstream"),
        "aiortc": _package_version("aiortc"),
        "av": _package_version("av"),
        "numpy": _package_version("numpy"),
        "scipy": _package_version("scipy"),
        "soundfile": _package_version("soundfile"),
        "getstream-rtc-core": _package_version("getstream-rtc-core"),
    }
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": _cpu_model(),
        "cpu_count": os.cpu_count(),
        "backend": detect_backend(),
        "library_versions": {k: v for k, v in versions.items() if v is not None},
    }


def percentile(samples: Iterable[float], p: float) -> Optional[float]:
    values = sorted(samples)
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    k = (len(values) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(values) - 1)
    if lo == hi:
        return float(values[lo])
    frac = k - lo
    return float(values[lo] + (values[hi] - values[lo]) * frac)


def summarize(
    name: str,
    samples: list[float],
    *,
    category: str,
    unit: str,
    higher_is_better: bool,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": name,
        "category": category,
        "unit": unit,
        "higher_is_better": higher_is_better,
        "n": len(samples),
        "samples": [float(s) for s in samples],
        "mean": float(statistics.fmean(samples)) if samples else None,
        "median": float(statistics.median(samples)) if samples else None,
        "p95": percentile(samples, 95),
        "min": float(min(samples)) if samples else None,
        "max": float(max(samples)) if samples else None,
    }
    if extra:
        result.update(extra)
    return result


def current_rss_bytes() -> int:
    pid = os.getpid()
    if sys.platform == "darwin":
        out = subprocess.check_output(
            ["ps", "-o", "rss=", "-p", str(pid)], text=True
        ).strip()
        return int(out) * 1024
    with open(f"/proc/{pid}/status", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    raise RuntimeError("unable to read process RSS")
