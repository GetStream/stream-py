# Getstream Python SDK

### Running tests

Clone the repo and sync

```
git clone git@github.com:GetStream/stream-py.git
uv sync --no-sources --all-packages --all-extras --dev
```

Run tests

```
uv run pytest -m "not integration" tests/ getstream/
```


### Check

Shortcut to ruff, mypy and non integration tests:

```
uv run python dev.py check
```

### Formatting

```
uv run ruff check --fix
```

### Mypy type checks

```
uv run mypy --install-types --non-interactive --exclude 'getstream/models/.*' .
```

## Release

Create a new release on Github, CI handles the rest. If you do need to do it manually follow these instructions:

```
rm -rf dist
git tag v0.0.15
uv run hatch version # this should show the right version
git push origin main --tags
uv build --all
uv publish
```