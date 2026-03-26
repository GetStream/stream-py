.DEFAULT_GOAL := help

# ── Pytest marker expression ───────────────────────────────────────
# Override on the command line:  make test MARKER="integration"
# Default excludes integration tests for everyday local development.
MARKER ?= not integration

# ── Video-related test paths (single source of truth) ──────────────
# When you add a new video test file, add it here. Both test (via
# --ignore) and test-video (via positional args) stay in sync.
VIDEO_PATHS := \
	getstream/video \
	tests/rtc \
	tests/test_audio_stream_track.py \
	tests/test_connection_manager.py \
	tests/test_connection_utils.py \
	tests/test_signaling.py \
	tests/test_video_examples.py \
	tests/test_video_integration.py \
	tests/test_video_openai.py \
	tests/test_webrtc_generation.py

# ── Manual tests (require local infrastructure, never run in CI) ───
MANUAL_PATHS := \
	tests/test_tracing_jaeger_manual.py \
	tests/test_metrics_prometheus_manual.py

# ── Derived ignore flags ──────────────────────────────────────────
VIDEO_IGNORE  := $(addprefix --ignore=,$(VIDEO_PATHS))
MANUAL_IGNORE := $(addprefix --ignore=,$(MANUAL_PATHS))

# ── Typecheck exclusions ──────────────────────────────────────────
TY_EXCLUDES := \
	--exclude "getstream/models/" \
	--exclude "getstream/video/rtc/pb/" \
	--exclude "**/rest_client.py" \
	--exclude "**/async_rest_client.py" \
	--exclude "getstream/chat/channel.py" \
	--exclude "getstream/chat/async_channel.py" \
	--exclude "getstream/chat/client.py" \
	--exclude "getstream/chat/async_client.py" \
	--exclude "getstream/common/client.py" \
	--exclude "getstream/common/async_client.py" \
	--exclude "getstream/moderation/client.py" \
	--exclude "getstream/moderation/async_client.py" \
	--exclude "getstream/video/client.py" \
	--exclude "getstream/video/async_client.py" \
	--exclude "getstream/video/call.py" \
	--exclude "getstream/video/async_call.py" \
	--exclude "getstream/feeds/client.py" \
	--exclude "getstream/feeds/feeds.py" \
	--exclude "getstream/stream.py"

# ── Targets ───────────────────────────────────────────────────────

.PHONY: test test-video test-all test-integration test-jaeger test-prometheus lint format typecheck check regen help

## Run non-video tests (chat, feeds, moderation, etc.)
test:
	uv run pytest -m "$(MARKER)" tests/ getstream/ $(VIDEO_IGNORE) $(MANUAL_IGNORE)

## Run video/WebRTC tests only
test-video:
	uv run pytest -m "$(MARKER)" $(VIDEO_PATHS)

## Run all tests (non-video + video), excluding manual tests
test-all:
	uv run pytest -m "$(MARKER)" tests/ getstream/ $(MANUAL_IGNORE)

## Run integration tests for both groups
test-integration:
	$(MAKE) test MARKER="integration"
	$(MAKE) test-video MARKER="integration"

## Run the Jaeger tracing manual test (requires local Jaeger on :4317)
test-jaeger:
	uv run pytest -m "integration" tests/test_tracing_jaeger_manual.py

## Run the Prometheus metrics manual test (requires telemetry deps)
test-prometheus:
	uv run pytest -m "integration" tests/test_metrics_prometheus_manual.py

## Run Ruff linter and formatter check
lint:
	uv run ruff check .
	uv run ruff format --check .

## Auto-fix lint issues and format
format:
	uv run ruff check --fix .
	uv run ruff format .

## Run ty type checker
typecheck:
	uvx ty@0.0.24 check getstream/ $(TY_EXCLUDES)

## Run full check: lint + typecheck + non-video tests
check: lint typecheck test

## Regenerate all generated code (OpenAPI + WebRTC protobuf)
regen:
	./generate.sh
	./generate_webrtc.sh

## Show available targets
help:
	@echo "Usage: make <target> [MARKER=\"...\"]"
	@echo ""
	@echo "Test targets:"
	@echo "  test              Non-video tests (default MARKER='not integration')"
	@echo "  test-video        Video/WebRTC tests only"
	@echo "  test-all          All tests except manual infrastructure tests"
	@echo "  test-integration  Integration tests (both non-video and video)"
	@echo "  test-jaeger       Jaeger tracing manual test (needs Docker Jaeger)"
	@echo "  test-prometheus   Prometheus metrics manual test (needs telemetry deps)"
	@echo ""
	@echo "Quality targets:"
	@echo "  lint              Ruff linter + format check"
	@echo "  format            Auto-fix lint issues and format code"
	@echo "  typecheck         ty type checker"
	@echo "  check             Full check: lint + typecheck + non-video tests"
	@echo ""
	@echo "Code generation:"
	@echo "  regen             Regenerate OpenAPI + WebRTC protobuf code"
