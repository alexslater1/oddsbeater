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

# Type-check with mypy.
typecheck:
    uv run --directory pipeline mypy

# Run the tests.
test:
    uv run --directory pipeline pytest
