"""The shared fetch: saving and reading back."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from pipeline.getters import common

FakeHttp = Callable[[int, str], list[str]]


def test_fetch_saves_record_and_reuses_it(raw_dir: Path, fake_http: FakeHttp) -> None:
    calls = fake_http(200, '{"a": 1}')

    first = common.fetch("src", "x/1", "https://example.test/x/1")
    second = common.fetch("src", "x/1", "https://example.test/x/1")

    assert first == second == {"a": 1}
    assert calls == ["https://example.test/x/1"]  # only one call
    record = json.loads((raw_dir / "src" / "x" / "1.json").read_text())
    assert record["status"] == 200
    assert record["url"] == "https://example.test/x/1"
    assert "retrieved_at" in record


def test_fetch_keeps_non_json_as_text(raw_dir: Path, fake_http: FakeHttp) -> None:
    fake_http(200, "Div,Date\nE0,01/01/26\n")
    body = common.fetch("src", "csv", "https://example.test/a.csv")
    assert body == "Div,Date\nE0,01/01/26\n"


def test_fetch_saves_404(raw_dir: Path, fake_http: FakeHttp) -> None:
    fake_http(404, "not found")
    common.fetch("src", "gone", "https://example.test/gone")
    assert (raw_dir / "src" / "gone.json").exists()


@pytest.mark.parametrize("status", [403, 429])
def test_fetch_stops_on_block(raw_dir: Path, fake_http: FakeHttp, status: int) -> None:
    fake_http(status, "")
    with pytest.raises(common.Blocked):
        common.fetch("src", "blocked", "https://example.test/b")
    assert not (raw_dir / "src" / "blocked.json").exists()
