"""SofaScore: each command's data, and where it's saved."""

import json
from pathlib import Path

from pipeline.getters import sofascore


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


def test_event_returns_every_match_endpoint_by_name(
    raw_dir: Path, pages: dict[str, str]
) -> None:
    for name, suffix in sofascore.MATCH_ENDPOINTS.items():
        pages[f"{sofascore.BASE_URL}/event/1{suffix}"] = json.dumps({"name": name})

    data = sofascore.event("1")

    assert data == {name: {"name": name} for name in sofascore.MATCH_ENDPOINTS}
    for suffix in sofascore.MATCH_ENDPOINTS.values():
        assert (raw_dir / "sofascore" / f"event/1{suffix}.json").exists()
