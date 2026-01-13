# Getstream Python SDK

### Running tests

Clone the repo and sync

```
git clone git@github.com:GetStream/stream-py.git
uv sync --no-sources --all-packages --all-extras --dev
```

Env setup

```
cp .env.example .env
```

Run tests

```
uv run pytest -m "not integration" tests/ getstream/
```

### Commit hook

```
pre-commit install
```

### Check

Shortcut to ruff, ty (type checker) and non integration tests:

```
uv run python dev.py
```

### Formatting

```
uv run ruff check --fix
```

### Type checking (ty)

Type checking is run via the `ty` type checker, excluding generated code:

```
uv run python dev.py ty
```

Or manually (note: requires exclude flags for generated code - see dev.py for the full list):
```
uvx ty check getstream/ --exclude "getstream/models/" --exclude "getstream/video/rtc/pb/" ...
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

## OpenAPI & Protobuf

Most API endpoints use openAPI definitions.
Part of the video endpoints use Protobuf.
Use these commands to regenerate:

```
./generate.sh
./generate_webrtc.sh
```

