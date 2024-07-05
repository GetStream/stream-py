# Python interpreter
PYTHON := python3

# Poetry
POETRY := poetry

# pipx
PIPX := pipx

# Virtual environment
VENV := .venv

# Source directory
SRC_DIR := getstream

# Test directory
TEST_DIR := tests

# Project name (assuming it's the same as the directory name)
PROJECT_NAME := getstream

# Default target
.DEFAULT_GOAL := help

# Docker image name
IMAGE_NAME := getstream-cli

# GitHub Container Registry
GHCR_REPO := ghcr.io/$(shell echo ${GITHUB_REPOSITORY} | tr '[:upper:]' '[:lower:]')

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  install    : Install project dependencies"
	@echo "  update     : Update project dependencies"
	@echo "  test       : Run tests"
	@echo "  lint       : Run linter"
	@echo "  fix        : Auto-fix linter issues"
	@echo "  format     : Format code"
	@echo "  clean      : Remove build artifacts and cache files"
	@echo "  run        : Run the CLI application"
	@echo "  pipx-install: Install the project globally using pipx"
	@echo "  pipx-uninstall: Uninstall the project from pipx"
	@echo "  build      : Build the project"
	@echo "  publish    : Publish the project to PyPI"
	@echo "  docker-build : Build Docker image"
	@echo "  docker-run   : Run Docker container (use CMD='command' to specify CLI command)"
	@echo "  docker-push  : Push Docker image to GitHub Container Registry"

.PHONY: install
install:
	$(POETRY) install

.PHONY: update
update:
	$(POETRY) update

.PHONY: test
test:
	$(POETRY) run pytest $(TEST_DIR)

.PHONY: lint
lint:
	$(POETRY) run ruff check $(SRC_DIR) $(TEST_DIR)

.PHONY: fix
fix:
	$(POETRY) run ruff check --fix $(SRC_DIR) $(TEST_DIR)

.PHONY: format
format:
	$(POETRY) run ruff format $(SRC_DIR) $(TEST_DIR)

.PHONY: clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf build dist *.egg-info

.PHONY: run
run:
	$(POETRY) run stream-cli

.PHONY: pipx-install
pipx-install:
	$(PIPX) install --editable .

.PHONY: pipx-uninstall
pipx-uninstall:
	$(PIPX) uninstall $(PROJECT_NAME)

.PHONY: build
build:
	$(POETRY) build

.PHONY: publish
publish:
	$(POETRY) publish

.PHONY: docker-build
docker-build:
	docker build -t $(IMAGE_NAME) .

.PHONY: docker-run
docker-run:
	docker run -e STREAM_API_KEY=$(STREAM_API_KEY) -e STREAM_API_SECRET=$(STREAM_API_SECRET) $(IMAGE_NAME) $(CMD)

.PHONY: docker-push
docker-push:
	docker tag $(IMAGE_NAME) $(GHCR_REPO):$(VERSION)
	docker push $(GHCR_REPO):$(VERSION)