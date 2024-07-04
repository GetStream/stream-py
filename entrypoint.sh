#!/bin/bash

# Check if required environment variables are set
if [[ -z "${STREAM_API_KEY}" || -z "${STREAM_API_SECRET}" ]]; then
    echo "Error: STREAM_API_KEY and STREAM_API_SECRET must be set"
    exit 1
fi

# Run the CLI command with all passed arguments
poetry run python -m getstream.cli "$@"