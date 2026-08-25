"""Compare two harness JSON result files.

Usage::

    uv run python -m benchmarks.compare baseline.json candidate.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {b["name"]: b for b in payload.get("benchmarks", [])}


def _fmt(value: Optional[float], digits: int = 3) -> str:
    if value is None:
        return "-"
    if abs(value) >= 1000:
        return f"{value:.1f}"
    if abs(value) >= 10:
        return f"{value:.2f}"
    return f"{value:.{digits}f}"


def _delta_pct(baseline: Optional[float], candidate: Optional[float]) -> Optional[float]:
    if baseline is None or candidate is None or baseline == 0:
        return None
    return (candidate - baseline) / abs(baseline) * 100.0


def _winner(
    higher_is_better: bool,
    baseline: Optional[float],
    candidate: Optional[float],
) -> str:
    if baseline is None or candidate is None:
        return "-"
    if candidate == baseline:
        return "tie"
    candidate_better = candidate > baseline if higher_is_better else candidate < baseline
    return "candidate" if candidate_better else "baseline"


def _row(
    name: str,
    unit: str,
    hib: bool,
    base: Optional[dict[str, Any]],
    cand: Optional[dict[str, Any]],
    stat: str,
) -> list[str]:
    b = None if base is None else base.get(stat)
    c = None if cand is None else cand.get(stat)
    d = _delta_pct(b, c)
    delta = "-" if d is None else f"{d:+.1f}%"
    return [
        name,
        unit,
        stat,
        _fmt(b),
        _fmt(c),
        delta,
        _winner(hib, b, c),
    ]


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for row in rows:
        print(fmt.format(*row))


def compare(baseline: dict[str, Any], candidate: dict[str, Any]) -> int:
    base_meta = baseline.get("metadata", {})
    cand_meta = candidate.get("metadata", {})
    print("Baseline : backend={backend} git={git_sha} python={python}".format(**{
        "backend": base_meta.get("backend", "?"),
        "git_sha": (base_meta.get("git_sha") or "?")[:12],
        "python": base_meta.get("python", "?"),
    }))
    print("Candidate: backend={backend} git={git_sha} python={python}".format(**{
        "backend": cand_meta.get("backend", "?"),
        "git_sha": (cand_meta.get("git_sha") or "?")[:12],
        "python": cand_meta.get("python", "?"),
    }))
    print()

    base_idx = _index(baseline)
    cand_idx = _index(candidate)
    names = sorted(set(base_idx) | set(cand_idx))
    headers = ["name", "unit", "stat", "baseline", "candidate", "delta", "winner"]
    rows: list[list[str]] = []
    for name in names:
        base = base_idx.get(name)
        cand = cand_idx.get(name)
        unit = (cand or base or {}).get("unit", "")
        hib = bool((cand or base or {}).get("higher_is_better", True))
        if base is None:
            rows.append([name, unit, "median", "missing", _fmt(cand.get("median")), "-", "-"])
            continue
        if cand is None:
            rows.append([name, unit, "median", _fmt(base.get("median")), "missing", "-", "-"])
            continue
        rows.append(_row(name, unit, hib, base, cand, "median"))
        rows.append(_row(name, unit, hib, base, cand, "p95"))
    _print_table(headers, rows)

    print()
    for label, payload in (("Baseline skipped", baseline), ("Candidate skipped", candidate)):
        skipped = payload.get("skipped") or []
        if skipped:
            print(f"{label}:")
            for item in skipped:
                print(f"  - {item['name']}: {item['reason']}")
    for label, payload in (("Baseline errors", baseline), ("Candidate errors", candidate)):
        errors = payload.get("errors") or []
        if errors:
            print(f"{label}:")
            for item in errors:
                print(f"  - {item['name']}: {item['reason']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="Baseline results JSON")
    parser.add_argument("candidate", type=Path, help="Candidate results JSON")
    args = parser.parse_args(argv)
    return compare(_load(args.baseline), _load(args.candidate))


if __name__ == "__main__":
    sys.exit(main())
