#!/usr/bin/env python3
"""
Development CLI tool for getstream SDK.
Essential dev commands for testing, linting, and type checking.
"""

import os
import shlex
import subprocess
import sys
from typing import Optional

import click


def run(
    command: str, env: Optional[dict] = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run a shell command with automatic argument parsing."""
    click.echo(f"Running: {command}")

    # Set up environment
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    cmd_list = shlex.split(command)
    try:
        result = subprocess.run(
            cmd_list, check=check, capture_output=False, env=full_env, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            click.echo(f"Command failed with exit code {e.returncode}", err=True)
            sys.exit(e.returncode)
        # Return a CompletedProcess with the error info when check=False
        return subprocess.CompletedProcess(
            cmd_list, e.returncode, stdout=None, stderr=None
        )


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Development CLI tool for getstream SDK. Runs 'check' by default."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(check)


@cli.command()
def test_integration():
    """Run integration tests (requires secrets in place)."""
    click.echo("Running integration tests...")
    run("uv run pytest -m integration tests/ getstream/")


@cli.command()
def test():
    """Run all tests except integration tests."""
    click.echo("Running unit tests...")
    run("uv run pytest -m 'not integration' tests/ getstream/")


@cli.command()
def format():
    """Run ruff formatting with auto-fix."""
    click.echo("Running ruff format...")
    run("uv run ruff check --fix .")
    run("uv run ruff format .")


@cli.command()
def lint():
    """Run ruff linting (check only)."""
    click.echo("Running ruff lint...")
    run("uv run ruff check .")
    run("uv run ruff format --check .")


# Generated code patterns to exclude from type checking
TY_EXCLUDES = [
    "getstream/models/",
    "getstream/video/rtc/pb/",
    "**/rest_client.py",
    "**/async_rest_client.py",
    "getstream/chat/channel.py",
    "getstream/chat/async_channel.py",
    "getstream/chat/client.py",
    "getstream/chat/async_client.py",
    "getstream/common/client.py",
    "getstream/common/async_client.py",
    "getstream/moderation/client.py",
    "getstream/moderation/async_client.py",
    "getstream/video/client.py",
    "getstream/video/async_client.py",
    "getstream/video/call.py",
    "getstream/video/async_call.py",
    "getstream/feeds/client.py",
    "getstream/feeds/feeds.py",
    "getstream/stream.py",
]


def _run_typecheck():
    """Internal function to run ty type checks."""
    click.echo("Running ty type checker on getstream...")
    excludes = " ".join(f'--exclude "{e}"' for e in TY_EXCLUDES)
    run(f"uvx ty check getstream/ {excludes}")


@cli.command()
def typecheck():
    """Run ty type checks on getstream package (excludes generated code)."""
    _run_typecheck()


@cli.command("ty")
def ty_alias():
    """Run ty type checks (alias for 'typecheck')."""
    _run_typecheck()


@cli.command()
def check():
    """Run full check: ruff, ty, and unit tests."""
    click.echo("Running full development check...")

    # Run ruff
    click.echo("\n=== 1. Ruff Linting ===")
    run("uv run ruff check .")
    run("uv run ruff format --check .")

    # Run ty type checker on main package (excludes generated code)
    click.echo("\n=== 2. Type Checking (ty) ===")
    excludes = " ".join(f'--exclude "{e}"' for e in TY_EXCLUDES)
    run(f"uvx ty check getstream/ {excludes}")

    # Run unit tests
    click.echo("\n=== 3. Unit Tests ===")
    run("uv run pytest -m 'not integration' tests/ getstream/")

    click.echo("\n✅ All checks passed!")


@cli.command()
def regen():
    """Regenerate all generated code (OpenAPI + WebRTC protobuf)."""
    click.echo("Regenerating all generated code...")

    click.echo("\n=== 1. OpenAPI Code Generation ===")
    run("./generate.sh")

    click.echo("\n=== 2. WebRTC Protobuf Generation ===")
    run("./generate_webrtc.sh")

    click.echo("\n✅ Code regeneration complete!")


if __name__ == "__main__":
    cli()
