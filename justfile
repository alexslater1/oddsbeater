# Install dependencies and git hooks.
setup:
    uv sync --directory pipeline
    uv run --directory pipeline pre-commit install

# Lint with Ruff.
lint:
    uv run --directory pipeline ruff check

# Format with Ruff.
fmt:
    uv run --directory pipeline ruff format

# Check formatting with Ruff.
fmt-check:
    uv run --directory pipeline ruff format --check

# Type-check with mypy.
typecheck:
    uv run --directory pipeline mypy

# Run the tests.
test:
    uv run --directory pipeline pytest

# Run all checks and formatting.
check: lint fmt typecheck test
