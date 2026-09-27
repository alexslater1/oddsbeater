# SofaScore: match data
#
# Data: Match details, lineups (predicted & confirmed), player statistics, shot maps,
# average positions, incidents, team statistics, managers, commentary and odds.
#
# How: Uses the JSON API behind the website (no key), 4 to 8 seconds apart. Keep it
# under 3,000 requests a day. Each response is saved once, under its API path,
# except a match's pre-match data, which is replaced 100 hours and 1 hour before
# kickoff. Between kickoff and settling, nothing is fetched.

from collections.abc import Collection
from datetime import UTC, datetime, timedelta
from typing import Any

from pipeline.getters import common

SOURCE = "sofascore"
BASE_URL = "https://www.sofascore.com/api/v1"
DELAY = (4, 8)

MATCH_ENDPOINTS = {
    # Teams with their managers, kickoff (startTimestamp), status, score, round,
    # venue, referee:
    "details": "",
    # Formation, missing players, and each player's shirt number, position and
    # player match statistics: minutesPlayed, fouls, wasFouled, totalShots,
    # onTargetScoringAttempt, totalTackle, expectedGoals … Predicted until confirmed:
    "lineups": "/lineups",
    # Every shot: player, playerCoordinates, xg, xgot, bodyPart, situation:
    "shotmap": "/shotmap",
    # Each player's averageX and averageY:
    "average-positions": "/average-positions",
    # Goals, cards, substitutions, periods and injury time, each with its time:
    "incidents": "/incidents",
    # Team statistics for the whole match (ALL) and each half (1ST, 2ND):
    "statistics": "/statistics",
    # Text commentary:
    "comments": "/comments",
    # One provider's markets, each choice with its opening and latest price:
    "odds": "/odds/1/all",
}

# The endpoints with data before kickoff.
PRE_MATCH = ("details", "lineups", "odds")

# Assumes times are correct and same for all competitions
PREDICTED_LINEUPS = timedelta(hours=100)
CONFIRMED_LINEUPS = timedelta(hours=1)


class NotReady(Exception):
    """The match is in play, not settled yet, or not played. Nothing is saved."""


def window(kickoff: datetime, at: datetime) -> int:
    """0 before predicted lineups, 1 once they're out, 2 once confirmed."""
    left = kickoff - at
    return (left <= PREDICTED_LINEUPS) + (left <= CONFIRMED_LINEUPS)


def saved_kickoff_time(pre_match_path: str) -> tuple[datetime, datetime] | None:
    """The saved pre-match copy's kickoff and when it was fetched, if saved."""
    if not common.location(SOURCE, pre_match_path).exists():
        return None
    saved = common.read(SOURCE, pre_match_path)
    kickoff = datetime.fromtimestamp(saved["body"]["event"]["startTimestamp"], UTC)
    return kickoff, datetime.fromisoformat(saved["retrieved_at"])


def read_all(folder: str, names: Collection[str]) -> dict[str, Any]:
    """A saved copy's bodies by name, read straight from disk."""
    return {
        name: common.read(SOURCE, folder + MATCH_ENDPOINTS[name])["body"]
        for name in names
    }


def request_all(
    match_path: str, folder: str, details: dict[str, Any], names: Collection[str]
) -> dict[str, Any]:
    """Request names' endpoints, save them under folder and return their bodies."""
    # The details are in hand already
    rest = [name for name in names if name != "details"]
    records = {"details": details}
    for name in rest:
        url = BASE_URL + match_path + MATCH_ENDPOINTS[name]
        records[name] = common.request(url, delay=DELAY)

    # Save only once every request has worked, and the details last: saved
    # details mean the whole copy is saved
    for name in [*rest, "details"]:
        common.save(SOURCE, folder + MATCH_ENDPOINTS[name], records[name])
    return {name: records[name]["body"] for name in names}


def endpoint(path: str) -> Any:
    """Any API path's JSON, such as /event/{event_id}/player/{player_id}/statistics"""
    path = "/" + path.strip("/")
    return common.fetch(SOURCE, path, BASE_URL + path, delay=DELAY)


def event(event_id: str) -> dict[str, Any]:
    """A match, once settled, gets each of MATCH_ENDPOINTS by name.
    Before kickoff, PRE_MATCH only, updated 100 hours and 1 hour before.
    In between, it raises NotReady."""
    match_path = f"/event/{event_id}"
    pre_match_path = f"{match_path}/pre-match"
    now = datetime.now(UTC)

    # Settled and saved, read it back
    if common.location(SOURCE, match_path).exists():
        return read_all(match_path, MATCH_ENDPOINTS)

    # Check if pre-match is saved
    saved = saved_kickoff_time(pre_match_path)
    if saved is not None:
        kickoff, fetched = saved
        # If still pre-match and same information window, read directly
        if now < kickoff and window(kickoff, fetched) == window(kickoff, now):
            return read_all(pre_match_path, PRE_MATCH)
        # If match in progress, do nothing
        if kickoff <= now and not common.settled(kickoff, now):
            raise NotReady(
                f"event {event_id} isn't settled yet, kickoff {kickoff:%Y-%m-%d %H:%M} UTC"
            )

    # Nothing saved, a new information window, or settled: fetch match details
    fetched_match_details = common.request(BASE_URL + match_path, delay=DELAY)
    info = fetched_match_details["body"]["event"]
    kickoff = datetime.fromtimestamp(info["startTimestamp"], UTC)
    status = info["status"]["type"]

    # If pre-match, get & save pre-match data
    if status == "notstarted" and now < kickoff:
        return request_all(match_path, pre_match_path, fetched_match_details, PRE_MATCH)

    # In play, not settled yet, or not played: save nothing
    if status != "finished" or not common.settled(kickoff, now):
        raise NotReady(
            f"event {event_id} is {status}, kickoff {kickoff:%Y-%m-%d %H:%M} UTC"
        )

    # Match settled, first time: get & save every endpoint
    return request_all(match_path, match_path, fetched_match_details, MATCH_ENDPOINTS)
