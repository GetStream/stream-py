# Python interpreter
PYTHON := python3

# Poetry
POETRY := poetry

# Virtual environment
VENV := .venv

# Source directory
SRC_DIR := getstream

# Test directory
TEST_DIR := tests

# Default target
.DEFAULT_GOAL := help

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
	$(POETRY) run cli