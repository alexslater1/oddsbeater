"""Smoke test: the pipeline package is installed and importable."""

import pipeline


def test_package_imports() -> None:
    assert pipeline.__name__ == "pipeline"
