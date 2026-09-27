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


def endpoint(path: str) -> Any:
    """Any API path's JSON, such as /event/{event_id}/player/{player_id}/statistics"""
    path = "/" + path.strip("/")
    return common.fetch(SOURCE, path, BASE_URL + path, delay=DELAY)
