"""Shared helpers for the RTC benchmark harness."""

from __future__ import annotations

import hashlib
import logging
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

logger = logging.getLogger("benchmarks")

# Canonical results come from idle Linux x86_64 (the production agent target).
CANONICAL_HOST_CLASS = "canonical-linux-x86_64"
WARN_LOAD_PER_CPU = 0.25
ABORT_LOAD_PER_CPU = 0.75


class LoadGuardError(RuntimeError):
    """Raised when 1-minute loadavg is too high for a canonical bench run."""


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
        return "unavailable"
    return "rust"


def host_class() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "linux" and machine in {"x86_64", "amd64"}:
        return CANONICAL_HOST_CLASS
    return "non-canonical"


def load_snapshot() -> dict[str, Any]:
    load1, load5, load15 = os.getloadavg()
    cpus = os.cpu_count() or 1
    return {
        "loadavg_1": load1,
        "loadavg_5": load5,
        "loadavg_15": load15,
        "cpu_count": cpus,
        "load_per_cpu": load1 / cpus,
    }


def check_load_guard() -> dict[str, Any]:
    """Warn or abort when the host is too busy for a trustworthy run."""
    snap = load_snapshot()
    load_per_cpu = float(snap["load_per_cpu"])
    allow = os.environ.get("STREAM_BENCH_ALLOW_LOAD", "").strip() in {"1", "true", "yes"}
    if load_per_cpu >= ABORT_LOAD_PER_CPU:
        message = (
            f"loadavg {snap['loadavg_1']:.2f} on {snap['cpu_count']} CPUs "
            f"({load_per_cpu:.2f}/CPU) exceeds abort threshold {ABORT_LOAD_PER_CPU:.2f}/CPU"
        )
        if allow:
            logger.warning("Load guard abort skipped via STREAM_BENCH_ALLOW_LOAD: %s", message)
        else:
            raise LoadGuardError(
                message + "; rerun on an idle host or set STREAM_BENCH_ALLOW_LOAD=1"
            )
    elif load_per_cpu >= WARN_LOAD_PER_CPU:
        logger.warning(
            "Host is busy: loadavg %.2f (%.2f/CPU). Canonical numbers need an idle machine.",
            snap["loadavg_1"],
            load_per_cpu,
        )
    snap["canonical"] = host_class() == CANONICAL_HOST_CLASS and load_per_cpu < WARN_LOAD_PER_CPU
    return snap


def _package_version(name: str) -> Optional[str]:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rtc_core_native_hash() -> Optional[str]:
    try:
        import getstream_rtc_core
    except ImportError:
        return None
    origin = Path(getstream_rtc_core.__file__).resolve()
    parent = origin.parent if origin.suffix == ".py" else origin.parent
    candidates: list[Path] = []
    if ".so" in origin.name or origin.suffix in {".so", ".dylib", ".pyd"}:
        candidates.append(origin)
    for pattern in (
        "getstream_rtc_core*.so",
        "getstream_rtc_core*.dylib",
        "getstream_rtc_core*.pyd",
        "_getstream_rtc_core*",
    ):
        candidates.extend(parent.glob(pattern))
    files = [p for p in candidates if p.is_file()]
    if not files:
        return None
    target = max(files, key=lambda p: p.stat().st_size)
    return f"sha256:{_sha256_file(target)}"
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
        "host_class": host_class(),
        "hostname": platform.node(),
        "system": platform.system(),
        "canonical": host_class() == CANONICAL_HOST_CLASS,
        "load": load_snapshot(),
        "getstream_rtc_core_version": _package_version("getstream-rtc-core"),
        "getstream_rtc_core_native_hash": _rtc_core_native_hash(),
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
