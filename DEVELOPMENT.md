# Getstream Python SDK

### Setup

Clone the repo and install dependencies:

```
git clone git@github.com:GetStream/stream-py.git
uv sync --no-sources --all-packages --all-extras --dev
cp .env.example .env   # fill in your Stream credentials
pre-commit install      # optional: enable commit hooks
```

### Running tests

Run `make help` to see all available targets. The most common ones:

```
make test          # non-video tests (chat, feeds, moderation, etc.)
make test-video    # video/WebRTC tests only
make test-all      # both of the above
```

Non-video and video tests are split because they require different Stream credentials.
The `MARKER` variable defaults to `"not integration"`. Override it for integration tests:

```
make test-integration              # runs both groups with -m "integration"
make test MARKER="integration"     # or target a single group
```

Two manual tests exist for local telemetry inspection (excluded from CI):

```
make test-jaeger       # requires local Jaeger (docker run ... jaegertracing/all-in-one)
make test-prometheus   # requires getstream[telemetry] deps
```

### Linting and type checking

```
make lint        # ruff check + format check
make typecheck   # ty type checker (excludes generated code)
```

To auto-fix lint issues and format:

```
make format
```

Run lint, typecheck, and non-video tests in one go:

```
make check
```

### Code generation

```
make regen    # regenerate OpenAPI + WebRTC protobuf code
```

### Legacy: dev.py

`dev.py` is an older CLI tool that predates the Makefile. It still works but does not
handle the video/non-video test split or manual test exclusions. Prefer `make` targets.

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

