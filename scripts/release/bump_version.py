#!/usr/bin/env python3
"""Compute the next release version from PR title/body or workflow_dispatch input.

Usage:
  scripts/release/bump_version.py \
      --title "feat: add x" --body-file "$PR_BODY_FILE" \
      --output "$GITHUB_OUTPUT"

  scripts/release/bump_version.py \
      --manual-bump patch \
      --output "$GITHUB_OUTPUT"

  scripts/release/bump_version.py \
      --manual-bump patch --use-current-version true \
      --output "$GITHUB_OUTPUT"

Outputs (written to --output or stdout) follow the convention shared with the
getstream-php / getstream-ruby / getstream-net / getstream-go / stream-sdk-java
bump scripts:

  should_release=true|false
  bump=major|minor|patch|none
  previous_version=X.Y.Z
  version=X.Y.Z
  tag=vX.Y.Z

Side effect: in auto and manual-with-bump modes, updates the `version` field in
the top-level [project] table of pyproject.toml.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

PYPROJECT_PATH = Path("pyproject.toml")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
VERSION_LINE_PATTERN = re.compile(
    r'^version\s*=\s*"(\d+\.\d+\.\d+)"\s*$',
    re.MULTILINE,
)


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return result.stdout.strip()


def find_latest_semver_tag() -> str:
    raw = run(["git", "tag", "--list"])
    if not raw:
        return "0.0.0"
    versions: list[tuple[int, int, int]] = []
    for line in raw.splitlines():
        candidate = line.strip().lstrip("v")
        if SEMVER_PATTERN.match(candidate):
            major, minor, patch = candidate.split(".")
            versions.append((int(major), int(minor), int(patch)))
    if not versions:
        return "0.0.0"
    versions.sort()
    return "{}.{}.{}".format(*versions[-1])


def determine_bump_type(title: str, body: str) -> str:
    title = title.strip()
    body = body.strip()
    breaking_re = re.compile(r"BREAKING[ -]CHANGES?", re.IGNORECASE)
    if breaking_re.search(title) or breaking_re.search(body):
        return "major"
    match = re.match(r"^([a-zA-Z]+)(\([^)]+\))?(!)?:", title)
    if not match:
        return "none"
    if match.group(3) == "!":
        return "major"
    type_ = match.group(1).lower()
    if type_ == "feat":
        return "minor"
    if type_ in {"fix", "bug"}:
        return "patch"
    return "none"


def increment_version(current: str, bump: str) -> str:
    major, minor, patch = (int(x) for x in current.split("."))
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return current


def read_pyproject_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = VERSION_LINE_PATTERN.search(text)
    if not match:
        raise RuntimeError(
            'Could not find a static `version = "X.Y.Z"` line in pyproject.toml'
        )
    return match.group(1)


def update_pyproject_version(path: Path, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    new_text, count = VERSION_LINE_PATTERN.subn(f'version = "{version}"', text, count=1)
    if count == 0:
        raise RuntimeError(
            'Could not update version line in pyproject.toml (expected `version = "X.Y.Z"`)'
        )
    path.write_text(new_text, encoding="utf-8")


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def resolve_body(args: argparse.Namespace) -> str:
    if args.body_file:
        return Path(args.body_file).read_text(encoding="utf-8")
    return args.body or ""


def write_outputs(output_path: str, entries: dict[str, str]) -> None:
    if not output_path:
        for key, value in entries.items():
            print(f"{key}={value}")
        return
    with open(output_path, "a", encoding="utf-8") as fh:
        for key, value in entries.items():
            fh.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="")
    parser.add_argument("--body", default="")
    parser.add_argument("--body-file", dest="body_file", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--manual-bump", dest="manual_bump", default="")
    parser.add_argument(
        "--use-current-version",
        dest="use_current_version",
        default="false",
    )
    args = parser.parse_args()

    manual = args.manual_bump.strip().lower()
    use_current = parse_bool(args.use_current_version)

    if manual:
        if manual not in {"major", "minor", "patch"}:
            print("manual-bump must be one of: major, minor, patch", file=sys.stderr)
            return 1
        previous = find_latest_semver_tag()
        if use_current:
            next_version = read_pyproject_version(PYPROJECT_PATH)
        else:
            next_version = increment_version(previous, manual)
            update_pyproject_version(PYPROJECT_PATH, next_version)
        write_outputs(
            args.output,
            {
                "should_release": "true",
                "bump": manual,
                "previous_version": previous,
                "version": next_version,
                "tag": f"v{next_version}",
            },
        )
        return 0

    body = resolve_body(args)
    bump = determine_bump_type(args.title, body)
    if bump == "none":
        write_outputs(
            args.output,
            {
                "should_release": "false",
                "bump": "none",
            },
        )
        return 0

    previous = find_latest_semver_tag()
    next_version = increment_version(previous, bump)
    update_pyproject_version(PYPROJECT_PATH, next_version)

    write_outputs(
        args.output,
        {
            "should_release": "true",
            "bump": bump,
            "previous_version": previous,
            "version": next_version,
            "tag": f"v{next_version}",
        },
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
