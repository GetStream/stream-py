#!/usr/bin/env bash

SOURCE_PATH=../chat

if [ ! -d $SOURCE_PATH ]
then
  echo "cannot find chat path on the parent folder (${SOURCE_PATH}), do you have a copy of the API source?";
  exit 1;
fi

if ! uv -V &> /dev/null
then
  echo "cannot find uv in path, did you setup this repo correctly?";
  exit 1;
fi

set -ex

# cd in API repo, generate new spec and then generate code from it
( cd $SOURCE_PATH ; make openapi ; go run ./cmd/chat-manager openapi generate-client --language python --spec ./releases/v2/serverside-api.yaml --output ../stream-py/getstream/ )

# lint + auto-fix, then format generated code with ruff (align with pre-commit)
uv run ruff check --fix getstream/ tests/
uv run ruff format getstream/ tests/
