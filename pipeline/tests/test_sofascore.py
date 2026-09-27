"""SofaScore: each command's data, and where it's saved."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from pipeline.getters import common, sofascore

# Kickoffs as time from now, from the thresholds so they hold if those change.
# Settled:
SETTLED = -(common.SETTLE + timedelta(hours=1))
# Kicked off, not settled yet:
UNSETTLED = -common.SETTLE / 2
# Predicted lineups out, not confirmed yet:
PREDICTED = (sofascore.PREDICTED_LINEUPS + sofascore.CONFIRMED_LINEUPS) / 2


def serve_match(pages: dict[str, str], status: str, kickoff: timedelta) -> None:
    """Serve match 1: its details, with a kickoff this far from now, lineups with
    a player, and a body naming each other endpoint."""
    for name, suffix in sofascore.MATCH_ENDPOINTS.items():
        pages[f"{sofascore.BASE_URL}/event/1{suffix}"] = json.dumps({"name": name})
    lineups = {"home": {"players": [{"shirtNumber": 9}]}, "away": {"players": []}}
    pages[f"{sofascore.BASE_URL}/event/1/lineups"] = json.dumps(lineups)
    start = int((datetime.now(UTC) + kickoff).timestamp())
    event = {"startTimestamp": start, "status": {"type": status}}
    pages[f"{sofascore.BASE_URL}/event/1"] = json.dumps({"event": event})


def edit_saved_pre_match(
    raw_dir: Path,
    *,
    kickoff: timedelta | None = None,
    fetched_ago: timedelta = timedelta(0),
) -> None:
    """Change the saved pre-match copy: its kickoff, as time from now, and when it
    was fetched, as time ago."""
    saved = raw_dir / "sofascore" / "event" / "1" / "pre-match.json"
    record = json.loads(saved.read_text())
    if kickoff is not None:
        start = int((datetime.now(UTC) + kickoff).timestamp())
        record["body"]["event"]["startTimestamp"] = start
    fetched = datetime.fromisoformat(record["retrieved_at"]) - fetched_ago
    record["retrieved_at"] = fetched.isoformat()
    saved.write_text(json.dumps(record))


# endpoint


def test_endpoint_reads_directly_if_saved_before(
    raw_dir: Path, pages: dict[str, str]
) -> None:
    saved = raw_dir / "sofascore" / "event" / "1" / "lineups.json"
    saved.parent.mkdir(parents=True)
    record = {"url": "u", "retrieved_at": "t", "status": 200, "body": {"home": {}}}
    saved.write_text(json.dumps(record, indent=2))

    assert sofascore.endpoint("/event/1/lineups") == {"home": {}}


def test_endpoint_saves_under_its_api_path_if_ok(
    raw_dir: Path, pages: dict[str, str]
) -> None:
    pages[f"{sofascore.BASE_URL}/event/1/lineups"] = '{"home": {}}'
    # trailing slash stripped
    assert sofascore.endpoint("/event/1/lineups/") == {"home": {}}
    assert (raw_dir / "sofascore" / "event" / "1" / "lineups.json").exists()


# event: settled


def test_event_saves_every_endpoint_once_settled(
    raw_dir: Path, pages: dict[str, str], sent: list[str]
) -> None:
    serve_match(pages, "finished", SETTLED)

    data = sofascore.event("1")

    assert list(data) == list(sofascore.MATCH_ENDPOINTS)
    urls = [
        f"{sofascore.BASE_URL}/event/1{s}" for s in sofascore.MATCH_ENDPOINTS.values()
    ]
    assert sorted(sent) == sorted(urls)  # each once
    assert data["shotmap"] == {"name": "shotmap"}
    for suffix in sofascore.MATCH_ENDPOINTS.values():
        assert (raw_dir / "sofascore" / f"event/1{suffix}.json").exists()


def test_event_reads_a_settled_match_back(raw_dir: Path, pages: dict[str, str]) -> None:
    serve_match(pages, "finished", SETTLED)
    first = sofascore.event("1")
    pages.clear()  # any request now fails
    assert sofascore.event("1") == first


def test_event_saves_nothing_if_a_request_fails(
    raw_dir: Path, pages: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    serve_match(pages, "finished", SETTLED)
    serve = common.http_get

    def http_get(url: str) -> tuple[int, str]:
        return (429, "") if url.endswith("/comments") else serve(url)

    monkeypatch.setattr(common, "http_get", http_get)

    with pytest.raises(common.Blocked):
        sofascore.event("1")
    assert not list(raw_dir.rglob("*"))


@pytest.mark.parametrize(
    ("status", "kickoff", "details"),
    [
        ("finished", SETTLED, "/event/1"),
        ("notstarted", PREDICTED, "/event/1/pre-match"),
    ],
)
def test_event_saves_the_details_last(
    raw_dir: Path,
    pages: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    kickoff: timedelta,
    details: str,
) -> None:
    # A copy's details are what show it's saved, so they must go in last
    serve_match(pages, status, kickoff)
    paths: list[str] = []
    save = common.save

    def record_path(source: str, path: str, record: dict[str, Any]) -> None:
        paths.append(path)
        save(source, path, record)

    monkeypatch.setattr(common, "save", record_path)

    sofascore.event("1")

    assert paths[-1] == details
    assert paths.count(details) == 1


# event: before kickoff


def test_event_saves_pre_match_endpoints_before_kickoff(
    raw_dir: Path, pages: dict[str, str], sent: list[str]
) -> None:
    serve_match(pages, "notstarted", timedelta(hours=2))

    data = sofascore.event("1")

    assert list(data) == list(sofascore.PRE_MATCH)
    suffixes = [sofascore.MATCH_ENDPOINTS[name] for name in sofascore.PRE_MATCH]
    urls = [f"{sofascore.BASE_URL}/event/1{s}" for s in suffixes]
    assert sorted(sent) == sorted(urls)  # each once
    for name in sofascore.PRE_MATCH:
        suffix = sofascore.MATCH_ENDPOINTS[name]
        assert (raw_dir / "sofascore" / f"event/1/pre-match{suffix}.json").exists()
    assert not (raw_dir / "sofascore" / "event" / "1.json").exists()


@pytest.mark.parametrize(
    ("left", "window"),
    [
        (sofascore.PREDICTED_LINEUPS + timedelta(seconds=1), 0),
        (sofascore.PREDICTED_LINEUPS, 1),
        (sofascore.CONFIRMED_LINEUPS + timedelta(seconds=1), 1),
        (sofascore.CONFIRMED_LINEUPS, 2),
        (timedelta(0), 2),
    ],
)
def test_window_changes_at_predicted_and_confirmed_lineups(
    left: timedelta, window: int
) -> None:
    kickoff = datetime(2026, 10, 10, 14, 0, tzinfo=UTC)
    assert sofascore.window(kickoff, kickoff - left) == window


def test_event_keeps_pre_match_data_within_a_window(
    raw_dir: Path, pages: dict[str, str]
) -> None:
    serve_match(pages, "notstarted", PREDICTED)
    first = sofascore.event("1")
    pages.clear()  # any request now fails

    assert sofascore.event("1") == first


def test_event_updates_pre_match_data_in_a_new_window(
    raw_dir: Path, pages: dict[str, str]
) -> None:
    serve_match(pages, "notstarted", PREDICTED)
    sofascore.event("1")
    # As if it was saved before predicted lineups were out
    edit_saved_pre_match(raw_dir, fetched_ago=sofascore.PREDICTED_LINEUPS)
    pages[f"{sofascore.BASE_URL}/event/1/lineups"] = '{"confirmed": true}'

    assert sofascore.event("1")["lineups"] == {"confirmed": True}
    lineups = raw_dir / "sofascore" / "event" / "1" / "pre-match" / "lineups.json"
    assert json.loads(lineups.read_text())["body"] == {"confirmed": True}
    pages.clear()  # now saved in the new window, a run makes no requests
    assert sofascore.event("1")["lineups"] == {"confirmed": True}


# event: after kickoff


def test_event_refuses_without_asking_until_the_saved_kickoff_settles(
    raw_dir: Path, pages: dict[str, str]
) -> None:
    serve_match(pages, "notstarted", timedelta(minutes=30))
    sofascore.event("1")
    edit_saved_pre_match(raw_dir, kickoff=UNSETTLED)
    pages.clear()  # any request now fails

    with pytest.raises(sofascore.NotReady):
        sofascore.event("1")


def test_event_asks_again_once_the_saved_kickoff_has_settled(
    raw_dir: Path, pages: dict[str, str]
) -> None:
    serve_match(pages, "notstarted", timedelta(minutes=30))
    sofascore.event("1")
    edit_saved_pre_match(raw_dir, kickoff=SETTLED)
    serve_match(pages, "finished", SETTLED)

    assert list(sofascore.event("1")) == list(sofascore.MATCH_ENDPOINTS)
    assert (raw_dir / "sofascore" / "event" / "1.json").exists()


@pytest.mark.parametrize(
    ("status", "kickoff"),
    [
        ("inprogress", -timedelta(hours=1)),
        ("finished", UNSETTLED),
        ("postponed", -timedelta(days=1)),
        ("notstarted", -timedelta(minutes=5)),  # kickoff delayed
    ],
)
def test_event_refuses_and_saves_nothing_in_between(
    raw_dir: Path, pages: dict[str, str], status: str, kickoff: timedelta
) -> None:
    serve_match(pages, status, kickoff)
    with pytest.raises(sofascore.NotReady):
        sofascore.event("1")
    assert not list(raw_dir.rglob("*"))
