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
) -> subprocess.CompletedProcess:
    """Run a shell command with automatic argument parsing."""
    click.echo(f"Running: {command}")

    # Set up environment
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    try:
        cmd_list = shlex.split(command)
        result = subprocess.run(
            cmd_list, check=check, capture_output=False, env=full_env, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            click.echo(f"Command failed with exit code {e.returncode}", err=True)
            sys.exit(e.returncode)
        return e


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Development CLI tool for getstream SDK."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


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


@cli.command()
def mypy():
    """Run mypy type checks on getstream package."""
    click.echo("Running mypy on getstream...")
    run("uv run mypy --install-types --non-interactive getstream")


@cli.command()
def check():
    """Run full check: ruff, mypy, and unit tests."""
    click.echo("Running full development check...")

    # Run ruff
    click.echo("\n=== 1. Ruff Linting ===")
    run("uv run ruff check .")
    run("uv run ruff format --check .")

    # Run mypy on main package
    click.echo("\n=== 2. MyPy Type Checking ===")
    run("uv run mypy --install-types --non-interactive getstream")

    # Run unit tests
    click.echo("\n=== 3. Unit Tests ===")
    run("uv run pytest -m 'not integration' tests/ getstream/")

    click.echo("\n✅ All checks passed!")


if __name__ == "__main__":
    cli()
