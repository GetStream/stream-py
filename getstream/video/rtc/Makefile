SFU_DIR := ../../../../video-sfu
TARGET_DIR := $(SFU_DIR)
OUTPUT_SO := libstreamvideo.so
OUTPUT_H := libstreamvideo.h
GO_SDK_PATH := $(shell realpath $(SFU_DIR)/videosdk)
BUILD_PATH := $(shell realpath $(SFU_DIR)/videosdk/bindings)
CURRENT_DIR := $(shell pwd)

PROTO_FILE := $(shell realpath $(SFU_DIR)/videosdk/bindings/pb/events.proto)
PROTO_PATH := $(shell dirname $(PROTO_FILE))
OUT_DIR := .

# Ensure Go and Protobuf tools are installed
check_tools:
	@command -v go >/dev/null 2>&1 || { echo >&2 "Go is not installed. Aborting."; exit 1; }
	@command -v protoc >/dev/null 2>&1 || { echo >&2 "Protobuf compiler is not installed. Install it with 'sudo apt install -y protobuf-compiler'. Aborting."; exit 1; }

# Build Go shared library
build_go: check_tools
	@echo "Navigating to target directory: $(TARGET_DIR)"
	@cd $(TARGET_DIR) && \
	bash -c "cd $(BUILD_PATH)/pb && bash generate.sh" && \
	echo "Building Go shared object and header file..." && \
	go build -o $(OUTPUT_SO) -buildmode=c-shared $(BUILD_PATH) && \
	cp $(OUTPUT_SO) $(OUTPUT_H) $(CURRENT_DIR)
	@if [ ! -f "$(CURRENT_DIR)/$(OUTPUT_SO)" ] || [ ! -f "$(CURRENT_DIR)/$(OUTPUT_H)" ]; then \
		echo "Error: Either $(OUTPUT_SO) or $(OUTPUT_H) was not generated."; \
		exit 1; \
	fi
	@echo "Successfully built and copied $(OUTPUT_SO) and $(OUTPUT_H) to $(CURRENT_DIR)"

# Generate Python protobuf code
generate_python: check_tools
	@echo "Generating Python code from $(PROTO_FILE)..."
	@mkdir -p ./pb
	@uv run protoc -I. -I$(PROTO_PATH) --python_betterproto_out=./pb/ $(PROTO_FILE)
	@if [ $$? -eq 0 ]; then \
		echo "Python code generated successfully."; \
	else \
		echo "Error generating Python code."; \
		exit 1; \
	fi

all: build_go generate_python

# Watch mode for Linux (using inotifywait)
watch_linux:
	@echo "Watching for file changes on Linux, excluding libstreamvideo.so and libstreamvideo.h..."
	@while inotifywait -e modify --exclude 'libstreamvideo\.so|libstreamvideo\.h' $(PROTO_FILE) $(BUILD_PATH) $(GO_SDK_PATH); do \
		echo "File changes detected. Rebuilding..."; \
		$(MAKE) all; \
	done

# Watch mode for macOS (using fswatch)
watch_macos:
	@echo "Watching for file changes on macOS, excluding libstreamvideo.so and libstreamvideo.h..."
	@fswatch --exclude 'libstreamvideo\.(so|h)$$' $(PROTO_FILE) $(BUILD_PATH) $(GO_SDK_PATH) | while read f; do \
		echo "File changes detected in: $$f"; \
		$(MAKE) all; \
	done

watch:
	@if [[ "$$(uname)" == "Linux" ]]; then \
		$(MAKE) watch_linux; \
	elif [[ "$$(uname)" == "Darwin" ]]; then \
		$(MAKE) watch_macos; \
	else \
		echo "Watch mode is not supported on this operating system."; \
	fi
