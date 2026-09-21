# Install dependencies
setup:
    uv sync --directory pipeline

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
