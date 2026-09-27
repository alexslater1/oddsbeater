# SofaScore: match data
#
# Data: Match details, lineups (predicted & confirmed), player statistics, shot maps,
# average positions, incidents, team statistics, managers, commentary and odds.
#
# How: Uses the JSON API behind the website (no key), 4 to 8 seconds apart. Keep it
# under 3,000 requests a day. Each response is saved once, under its API path.

from typing import Any

from pipeline.getters import common

SOURCE = "sofascore"
BASE_URL = "https://www.sofascore.com/api/v1"
DELAY = (4, 8)

MATCH_ENDPOINTS = {
    # Teams, kickoff (startTimestamp), status, score, round, venue, referee:
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
    # homeManager and awayManager:
    "managers": "/managers",
    # Text commentary:
    "comments": "/comments",
    # One provider's markets, each choice with its opening and latest price:
    "odds": "/odds/1/all",
}


def endpoint(path: str) -> Any:
    """Any API path's JSON, such as /event/{event_id}/player/{player_id}/statistics"""
    path = "/" + path.strip("/")
    return common.fetch(SOURCE, path, BASE_URL + path, delay=DELAY)


def event(event_id: str) -> dict[str, Any]:
    """A match, as each of MATCH_ENDPOINTS by name."""
    return {
        name: endpoint(f"/event/{event_id}{suffix}")
        for name, suffix in MATCH_ENDPOINTS.items()
    }
