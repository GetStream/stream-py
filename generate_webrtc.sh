#!/usr/bin/env bash

# Exit on error
set -e

# Define constants
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROTOCOL_DIR="${SCRIPT_DIR}/protocol"
OUTPUT_DIR="${SCRIPT_DIR}/getstream/video/rtc/pb"
PROTO_DIR="${PROTOCOL_DIR}/protobuf"
SFU_SIGNAL_DIR="${PROTO_DIR}/video/sfu/signal_rpc"
MODELS_DIR="${PROTO_DIR}/video/sfu/models"
EVENTS_DIR="${PROTO_DIR}/video/sfu/event"

# Check if the protocol submodule exists, add it if not
if ! git submodule status | grep -q "protocol"; then
    echo "Protocol submodule not found. Adding it..."
    git submodule add -f https://github.com/GetStream/protocol
fi

# Update protocol submodule to latest version
echo "Updating protocol submodule..."
git submodule update --init --recursive
(cd "${PROTOCOL_DIR}" && git checkout main && git pull)

# Make sure output directory exists and clear previous generated files
echo "Preparing output directory..."
mkdir -p "${OUTPUT_DIR}"
find "${OUTPUT_DIR}" -type f -not -name "__init__.py" -delete

# Make sure __init__.py exists in output directory
touch "${OUTPUT_DIR}/__init__.py"

# Install Python dependencies
echo "Installing Python dependencies..."
uv sync --all-extras --dev --all-packages

# Ensure Go tools are available for Twirp
if ! command -v go &> /dev/null; then
    echo "go is not installed. Please install it to generate Twirp client code."
    exit 1
fi

# Ensure that Go path is in path otherwise protoc will not
if ! echo "$PATH" | grep -q "$(go env GOPATH)/bin"; then
    echo "$(go env GOPATH)/bin is not in PATH"
    exit 1
fi

echo "Installing protoc-gen-twirpy..."
go install github.com/tbarbugli/twirpy/protoc-gen-twirpy@423caa6

# Use grpcio-tools bundled protoc to ensure version consistency with the project's protobuf package
# This avoids version mismatches between system protoc and the Python protobuf runtime
# NOTE: grpcio-tools is pinned in pyproject.toml - update both when upgrading protobuf
run_protoc() {
    uv run python -m grpc_tools.protoc "$@"
}

# Get the path to the protoc-gen-mypy plugin using Python
PROTOC_GEN_MYPY_PATH=$(uv run python3 -c "import mypy_protobuf; import os; print(os.path.dirname(mypy_protobuf.__file__))")
if [ ! -d "$PROTOC_GEN_MYPY_PATH" ]; then
    echo "Error: protoc-gen-mypy not found at ${PROTOC_GEN_MYPY_PATH}"
    exit 1
fi

# Create a wrapper script for protoc-gen-mypy
WRAPPER_DIR=$(mktemp -d)
trap 'rm -rf "$WRAPPER_DIR"' EXIT
WRAPPER_SCRIPT="${WRAPPER_DIR}/protoc-gen-mypy"
cat > "${WRAPPER_SCRIPT}" << EOF
#!/bin/bash
exec uv run python3 -m mypy_protobuf.main
EOF
chmod +x "${WRAPPER_SCRIPT}"

# Create a temporary directory for generated code
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR" "$WRAPPER_DIR"' EXIT

# Create proper directory structure in temp dir
mkdir -p "${TMP_DIR}/stream/video/sfu/models"
mkdir -p "${TMP_DIR}/stream/video/sfu/signal_rpc"
mkdir -p "${TMP_DIR}/stream/video/sfu/event"

# Generate the protobuf Python files with correct package structure and type annotations
PYTHONPATH="${PYTHONPATH}:${TMP_DIR}" run_protoc \
    -I="${PROTO_DIR}" \
    --python_out="${TMP_DIR}/stream" \
    --plugin=protoc-gen-mypy="${WRAPPER_SCRIPT}" \
    --mypy_out="${TMP_DIR}/stream" \
    "${MODELS_DIR}/models.proto" \
    "${SFU_SIGNAL_DIR}/signal.proto" \
    "${EVENTS_DIR}/events.proto"

# Generate Twirp client for the Signal service
run_protoc \
    -I="${PROTO_DIR}" \
    --twirpy_out="${TMP_DIR}/stream" \
    "${SFU_SIGNAL_DIR}/signal.proto"

# Create proper directory structure in output dir
mkdir -p "${OUTPUT_DIR}/stream/video/sfu/models"
mkdir -p "${OUTPUT_DIR}/stream/video/sfu/signal_rpc"
mkdir -p "${OUTPUT_DIR}/stream/video/sfu/event"

# Create __init__.py files in all directories
find "${OUTPUT_DIR}" -type d -exec touch {}/__init__.py \;

# Copy generated files to the final location
cp -r "${TMP_DIR}/stream/video" "${OUTPUT_DIR}/stream/"

# Fix import paths in generated files
echo "Fixing import paths in generated files..."
find "${OUTPUT_DIR}" -type f -name "*.py" -exec sed -i '' 's/from video\.sfu/from getstream.video.rtc.pb.stream.video.sfu/g' {} \;

# Format generated code with ruff
echo "Formatting generated code with ruff..."
uv run ruff format "${OUTPUT_DIR}"

echo "WebRTC code generation complete. Generated files in ${OUTPUT_DIR}"
