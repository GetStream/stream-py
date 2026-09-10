## Project setup

1. This project uses `uv`, `pyproject.toml` and venv to manage dependencies.
2. Never use pip directly; use `uv add` for dependencies and `uv sync --dev --all-packages` to install.
3. Do not hand-edit generated Python. `./generate.sh` rebuilds API endpoints and models; `./generate_webrtc.sh` rebuilds WebRTC protobuf.
4. WebRTC / audio / video extras live in the `webrtc` optional group. Plugins that need them should depend on `getstream[webrtc]`.

Official Python SDK for Stream Chat, Video, Feeds, and Moderation.

- Default branch: `main`
- PyPI: `getstream` (`pyproject.toml` name/version)
- Requires Python `>=3.10,<4.0.0`; CI matrix 3.10–3.14
- Clone sibling of the chat monorepo as `../chat` (required for OpenAPI regen)
- `protocol/` is a git submodule (WebRTC protobuf regen)

More setup detail: `DEVELOPMENT.md`.

## Layout

Generated REST: `getstream/models/`, `**/rest_client.py`, `**/async_rest_client.py`, and generated client modules listed in the Makefile `TY_EXCLUDES` (chat/common/moderation/video/feeds clients, `getstream/stream.py`, etc.). WebRTC protobuf: `getstream/video/rtc/pb/`.

Handwritten: `getstream/base.py`, `config.py`, `exceptions.py`, `webhook.py`, `logging_utils.py`, tests, plugins.

- Tests: `tests/` (pytest also collects `getstream/`)
- Assets: `tests/assets/` (keep new files ≤ 256 KB)
- Webhook fixtures: `tests/assets/webhooks/`
- Manual (never CI): `tests/test_tracing_jaeger_manual.py`, `tests/test_metrics_prometheus_manual.py`

## Local commands

```bash
uv sync --no-sources --all-packages --all-extras --dev
cp .env.example .env
make test              # non-video; MARKER default "not integration"
make test-video
make test-all
make test-integration   # MARKER=integration for both groups
make lint
make format
make typecheck
make check             # lint + typecheck + non-video tests
make regen             # ./generate.sh && ./generate_webrtc.sh
```

Prefer `make` over `dev.py`. Always run pytest from the repo root (`uv run pytest` or `make test`).

Non-video vs video tests use different Stream apps (video credentials must have video enabled).

## Python testing

1. pytest; preferences in `pytest.ini`.
2. Fixtures inject clients; credentials from `.env`.
3. Use test classes for related cases. No mocks unless asked.
4. Marker `integration` for live API tests.

## OpenAPI regen

`./generate.sh`:

1. Requires `uv` and `../chat`.
2. `make openapi` in chat, then `./build/chat-manager openapi generate-client --language python --spec ./releases/v2/serverside-api.yaml --output ../stream-py/getstream/`.
3. Webhook fixtures into `tests/assets/webhooks` (`--time-format=unix-ns`).
4. `uv run ruff check --fix` + `ruff format` on `getstream/` and `tests/`.

`./generate_webrtc.sh` needs the `protocol` submodule. Generator tooling is internal.

Additive OpenAPI regen = **minor**. Title `feat: …`, not `feat!:`, unless the public Python API actually breaks.

## CI

`.github/workflows/ci.yml` (`CI (unit)`): calls `run_tests.yml` with `marker: 'not integration'`.

`.github/workflows/run_tests.yml` (`_run-tests`): ruff, ty typecheck, then:

- `test-non-video`: environment `ci`; `STREAM_CHAT_API_KEY` / `STREAM_CHAT_API_SECRET` / `STREAM_CHAT_BASE_URL`
- `test-video`: environment `ci`; `STREAM_API_KEY` / `STREAM_API_SECRET` / `STREAM_BASE_URL`

`.github/workflows/release.yml` (`Release`): merged PR to `main`, or `workflow_dispatch`. Publish job uses environment `pypi` and PyPI Trusted Publishing (`id-token: write`, `uv publish`).

Vars: `STREAM_CHAT_API_KEY`, `STREAM_CHAT_BASE_URL`, `STREAM_API_KEY`, `STREAM_BASE_URL`.
Secrets: `STREAM_CHAT_API_SECRET`, `STREAM_API_SECRET`.

Known flakes: live Chat API 503 if the CI app is on a bad shard.

## Release

Tags: `vX.Y.Z`. Publishes to PyPI via OIDC (`uv build` + `uv publish`). Version bump is committed locally for the tag only and **not** pushed to protected `main` (`scripts/release/bump_version.py` uses latest semver tag).

- `feat:` → minor; `fix:`/`bug:` → patch; `!:` in the conventional title → major. Other prefixes do not release.
- Fallback: Actions → **Release** with `version_bump` / `use_current_version`.
- Pipeline: unit + integration matrices, then tag, build, publish, GitHub Release.

README still mentions `BREAKING CHANGE` in the body; `bump_version.py` only honors the `!` marker on the title.

## PR conventions

Conventional titles drive the bump. Example regen: `feat: regenerate from OpenAPI`. Keep `docs:` / `chore:` / `test:` if you must not publish.
