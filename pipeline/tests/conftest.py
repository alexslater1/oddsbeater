"""Fixtures shared by the getter tests."""

import time
from collections.abc import Callable
from pathlib import Path

import pytest

from pipeline.getters import common


@pytest.fixture
def raw_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Save to a temporary directory. Mocks data/."""
    monkeypatch.setattr(common, "RAW_DIR", tmp_path)
    monkeypatch.setattr(time, "sleep", lambda _: None)
    return tmp_path


@pytest.fixture
def pages(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Pages to serve by URL. Mocks the network."""
    served: dict[str, str] = {}
    monkeypatch.setattr(time, "sleep", lambda _: None)

    def http_get(url: str) -> tuple[int, str]:
        return 200, served[url]

    monkeypatch.setattr(common, "http_get", http_get)
    return served


@pytest.fixture
def sent(pages: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """The URLs requested from pages, in order."""
    urls: list[str] = []
    serve = common.http_get

    def http_get(url: str) -> tuple[int, str]:
        urls.append(url)
        return serve(url)

    monkeypatch.setattr(common, "http_get", http_get)
    return urls


@pytest.fixture
def fake_http(monkeypatch: pytest.MonkeyPatch) -> Callable[[int, str], list[str]]:
    """Call with status and text, returns list of URLs. Mocks the network."""
    monkeypatch.setattr(time, "sleep", lambda _: None)

    def answer(status: int, text: str) -> list[str]:
        calls: list[str] = []

        def http_get(url: str) -> tuple[int, str]:
            calls.append(url)
            return status, text

        monkeypatch.setattr(common, "http_get", http_get)
        return calls

    return answer
