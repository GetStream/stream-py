#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
DST_PATH=$(pwd)
SOURCE_PATH=${SOURCE_PATH:-../chat}
FIXTURES_DIR=tests/assets/webhooks

WORK=$(mktemp -d)
cleanup() {
  git -C "$SOURCE_PATH" worktree remove --force "$WORK/chat" 2>/dev/null || true
  rm -rf "$WORK"
}
trap cleanup EXIT

# The spec comes from a protocol release, so the generated code always matches a tag anyone can regenerate from. SPEC_TAG=openapi-vX picks that release instead of the latest.
SPEC_TAG=${SPEC_TAG:-$(curl -fsSL -H "Accept: application/vnd.github+json" https://api.github.com/repos/GetStream/protocol/releases \
  | jq -r 'map(select(.tag_name | startswith("openapi-"))) | .[0].tag_name')}
[ -n "$SPEC_TAG" ] && [ "$SPEC_TAG" != "null" ] || { echo "could not resolve the latest protocol openapi release"; exit 1; }
SPEC_FILE=$WORK/serverside-api.yaml
curl -fsSL -o "$SPEC_FILE" "https://raw.githubusercontent.com/GetStream/protocol/${SPEC_TAG}/openapi/v2/serverside-api.yaml"

set -x

# GENERATOR_BIN=<path> runs an openapi binary attached to a chat release, so no chat checkout is needed; .spec-version records the version it reports.
# Otherwise the generator is built from chat at the spec's own tag, so the templates match the breaking-change list the regen PR check reads from that spec.
# GENERATOR_REF=HEAD builds from the ../chat checkout as it is, for an unreleased generator fix; the regen PR then has to be a major.
if [ -n "${GENERATOR_BIN:-}" ]; then
  GENERATOR=$(cd "$(dirname "$GENERATOR_BIN")" && pwd)/$(basename "$GENERATOR_BIN")
  GENERATOR_VERSION=$("$GENERATOR" --version)
  GENERATOR_VERSION=${GENERATOR_VERSION##* }
else
  [ -d "$SOURCE_PATH" ] || { echo "cannot find chat path on the parent folder (${SOURCE_PATH}), do you have a copy of the API source?"; exit 1; }
  GENERATOR_REF=${GENERATOR_REF:-${SPEC_TAG#openapi-}}
  GENERATOR_PATH=$SOURCE_PATH
  if [ "$GENERATOR_REF" != HEAD ]; then
    git -C "$SOURCE_PATH" fetch -q origin tag "$GENERATOR_REF"
    GENERATOR_PATH=$WORK/chat
    git -C "$SOURCE_PATH" worktree add -q --detach "$GENERATOR_PATH" "$GENERATOR_REF"
  fi
  make -C "$GENERATOR_PATH/tools/openapi" build
  GENERATOR=$(cd "$GENERATOR_PATH" && pwd)/build/openapi
  GENERATOR_VERSION=$(git -C "$GENERATOR_PATH" describe --tags --always --dirty)
fi

"$GENERATOR" generate-client --language python --spec "$SPEC_FILE" --output "$DST_PATH/getstream/"

# Webhook events dropped from the spec would otherwise leave stale fixtures behind.
rm -rf "$FIXTURES_DIR"
"$GENERATOR" generate-webhook-fixtures --output "$DST_PATH/$FIXTURES_DIR" --time-format=unix-ns

printf 'spec: %s\ngenerator: chat %s\n' "$SPEC_TAG" "$GENERATOR_VERSION" > .spec-version

# Same fixes and formatting as pre-commit, so the generated code passes the lint check.
uv run --frozen ruff check --fix getstream/ tests/
uv run --frozen ruff format getstream/ tests/
