"""Shared helpers for the RTC benchmark harness."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import platform
import statistics
import subprocess
import sys
import time
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
NETEM_PROFILES = ("clean", "loss-1pct", "loss-5pct", "cap-1mbps", "rtt-200ms")


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


def video_codec() -> str:
    """Publish codec for the Rust stack. Default VP9; STREAM_BENCH_VIDEO_CODEC=vp8 for diagnostics."""
    raw = os.environ.get("STREAM_BENCH_VIDEO_CODEC", "vp9").strip().lower()
    if raw in {"vp8", "vp9", "h264"}:
        return raw
    return "vp9"


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


def _is_native_lib(path: Path) -> bool:
    if not path.is_file():
        return False
    name = path.name
    return path.suffix in {".so", ".dylib", ".pyd"} or ".so" in name


def _rtc_core_native_hash() -> Optional[str]:
    try:
        import getstream_rtc_core
    except ImportError:
        return None
    origin = Path(getstream_rtc_core.__file__).resolve()
    parent = origin.parent
    candidates: list[Path] = []
    if _is_native_lib(origin):
        candidates.append(origin)
    for pattern in ("*.so", "*.dylib", "*.pyd", "_native*"):
        candidates.extend(parent.glob(pattern))
    files = [p for p in candidates if _is_native_lib(p)]
    if not files:
        return None
    target = max(files, key=lambda p: p.stat().st_size)
    return f"sha256:{_sha256_file(target)}"


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


def collect_metadata(*, netem_profile: str = "clean") -> dict[str, Any]:
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
        "video_codec": video_codec(),
        "host_class": host_class(),
        "system": platform.system(),
        "canonical": host_class() == CANONICAL_HOST_CLASS,
        "netem_profile": netem_profile,
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


def current_nthreads() -> int:
    pid = os.getpid()
    if sys.platform == "darwin":
        out = subprocess.check_output(
            ["ps", "-M", "-p", str(pid)], text=True
        )
        # Header plus one line per thread.
        return max(len(out.strip().splitlines()) - 1, 1)
    with open(f"/proc/{pid}/status", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("Threads:"):
                return int(line.split()[1])
    raise RuntimeError("unable to read thread count")


def rusage_maxrss_bytes() -> int:
    import resource

    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return int(rss)
    return int(rss) * 1024


STATS_POLL_HZ = 1.0

_OUTBOUND_RTP_FIELDS = ("packetsSent", "bytesSent", "nackCount", "pliCount", "firCount")
_REMOTE_INBOUND_RTP_FIELDS = ("packetsLost", "fractionLost", "roundTripTime")
_CANDIDATE_PAIR_FIELDS = ("availableOutgoingBitrate",)
UNMEASURABLE_UPSTREAM_FIELDS = (
    "retransmittedPacketsSent",
    "targetBitrate",
    "framesEncoded",
    "keyFramesEncoded",
    "jitter",
)


def _snake(name: str) -> str:
    out = []
    for ch in name:
        if ch.isupper():
            out.append("_")
            out.append(ch.lower())
        else:
            out.append(ch)
    return "".join(out)


def stat_get(record: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in record and record[name] is not None:
            return record[name]
        snake = _snake(name)
        if snake in record and record[snake] is not None:
            return record[snake]
    return None


def iter_stat_records(snapshot: Any, *, side: str = "publisher") -> list[dict[str, Any]]:
    if snapshot is None:
        return []
    payload = snapshot.get(side) if isinstance(snapshot, dict) else snapshot
    if isinstance(payload, dict):
        if "type" in payload or "id" in payload:
            records = [payload]
        else:
            records = [v for v in payload.values() if isinstance(v, dict)]
    elif isinstance(payload, list):
        records = [v for v in payload if isinstance(v, dict)]
    else:
        return []
    return records


def outbound_rtp_totals(
    snapshot: Any, *, kind: Optional[str] = None
) -> dict[str, float]:
    totals = {field: 0.0 for field in _OUTBOUND_RTP_FIELDS}
    found = False
    for rec in iter_stat_records(snapshot, side="publisher"):
        rec_type = rec.get("type")
        if rec_type not in {"outbound-rtp", "outbound_rtp"}:
            continue
        media = stat_get(rec, "kind", "mediaType")
        if kind is not None and media is not None and media != kind:
            continue
        found = True
        for field in _OUTBOUND_RTP_FIELDS:
            value = stat_get(rec, field)
            if value is not None:
                totals[field] += float(value)
    totals["present"] = 1.0 if found else 0.0
    return totals


def remote_inbound_rtp_summary(
    snapshot: Any, *, kind: Optional[str] = None
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "packetsLost": 0.0,
        "fractionLost": 0.0,
        "roundTripTime": None,
        "present": 0.0,
    }
    rtts: list[float] = []
    fractions: list[float] = []
    found = False
    for rec in iter_stat_records(snapshot, side="publisher"):
        rec_type = rec.get("type")
        if rec_type not in {"remote-inbound-rtp", "remote_inbound_rtp"}:
            continue
        media = stat_get(rec, "kind", "mediaType")
        if kind is not None and media is not None and media != kind:
            continue
        found = True
        lost = stat_get(rec, "packetsLost")
        if lost is not None:
            summary["packetsLost"] += float(lost)
        frac = stat_get(rec, "fractionLost")
        if frac is not None:
            fractions.append(float(frac))
        rtt = stat_get(rec, "roundTripTime")
        if rtt is not None:
            rtts.append(float(rtt))
    summary["present"] = 1.0 if found else 0.0
    if fractions:
        summary["fractionLost"] = max(fractions)
    if rtts:
        summary["roundTripTime"] = rtts[-1]
    return summary


def candidate_pair_summary(snapshot: Any) -> dict[str, Any]:
    best_bitrate: Optional[float] = None
    found = False
    for rec in iter_stat_records(snapshot, side="publisher"):
        rec_type = rec.get("type")
        if rec_type not in {"candidate-pair", "candidate_pair"}:
            continue
        found = True
        bitrate = stat_get(rec, "availableOutgoingBitrate")
        if bitrate is None:
            continue
        bitrate_f = float(bitrate)
        nominated = stat_get(rec, "nominated")
        state = stat_get(rec, "state")
        preferred = nominated or state in {"succeeded", "in-progress"}
        if preferred and (best_bitrate is None or bitrate_f > best_bitrate):
            best_bitrate = bitrate_f
        elif best_bitrate is None:
            best_bitrate = bitrate_f
    return {
        "availableOutgoingBitrate": best_bitrate,
        "present": 1.0 if found else 0.0,
    }


def gap_metrics(snapshot: Any, *, kind: Optional[str] = None) -> dict[str, Any]:
    outbound = outbound_rtp_totals(snapshot, kind=kind)
    inbound = remote_inbound_rtp_summary(snapshot, kind=kind)
    pair = candidate_pair_summary(snapshot)
    return {
        "packetsSent": outbound["packetsSent"],
        "bytesSent": outbound["bytesSent"],
        "nackCount": outbound["nackCount"],
        "pliCount": outbound["pliCount"],
        "firCount": outbound["firCount"],
        "packetsLost": inbound["packetsLost"],
        "fractionLost": inbound["fractionLost"],
        "roundTripTime": inbound["roundTripTime"],
        "availableOutgoingBitrate": pair["availableOutgoingBitrate"],
        "stats_gap": classify_rtc_stats(snapshot),
    }


def classify_rtc_stats(snapshot: Any) -> dict[str, Any]:
    records = iter_stat_records(snapshot, side="publisher")
    records.extend(iter_stat_records(snapshot, side="subscriber"))
    expected = {
        "outbound-rtp": list(_OUTBOUND_RTP_FIELDS),
        "remote-inbound-rtp": list(_REMOTE_INBOUND_RTP_FIELDS),
        "candidate-pair": list(_CANDIDATE_PAIR_FIELDS),
    }
    populated = {key: [] for key in expected}
    missing = {key: list(fields) for key, fields in expected.items()}
    types_seen: list[str] = []
    unmeasurable_present: list[str] = []
    for rec in records:
        rec_type = rec.get("type")
        if rec_type and rec_type not in types_seen:
            types_seen.append(rec_type)
        for field in UNMEASURABLE_UPSTREAM_FIELDS:
            if stat_get(rec, field) is not None and field not in unmeasurable_present:
                unmeasurable_present.append(field)
        expected_type = rec_type
        if rec_type == "outbound_rtp":
            expected_type = "outbound-rtp"
        elif rec_type == "remote_inbound_rtp":
            expected_type = "remote-inbound-rtp"
        elif rec_type == "candidate_pair":
            expected_type = "candidate-pair"
        fields = expected.get(expected_type)
        if not fields:
            continue
        for field in fields:
            if stat_get(rec, field) is None:
                continue
            if field not in populated[expected_type]:
                populated[expected_type].append(field)
            if field in missing[expected_type]:
                missing[expected_type].remove(field)
    return {
        "populated": populated,
        "missing_expected": missing,
        "unmeasurable_upstream": list(UNMEASURABLE_UPSTREAM_FIELDS),
        "unmeasurable_actually_present": unmeasurable_present,
        "types_seen": types_seen,
    }


async def poll_stats(
    connection: Any, stop: asyncio.Event, *, interval: float = STATS_POLL_HZ
) -> list[dict[str, Any]]:
    """Poll ConnectionManager.stats() until `stop` is set (default 1 Hz)."""
    samples: list[dict[str, Any]] = []
    while not stop.is_set():
        snapshot = await connection.stats()
        samples.append({"t": time.monotonic(), "stats": snapshot})
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass
    snapshot = await connection.stats()
    samples.append({"t": time.monotonic(), "stats": snapshot})
    return samples
