# fetch() gets a URL's data in three steps:
# 1. location(): if data/raw/{source}/{path}.json is saved already, read it back.
# 2. request(): otherwise wait a random delay, request the URL with Chrome
#    impersonation, and return the response as {url, retrieved_at, status, body}.
# 3. save(): write that record to data/raw/{source}/{path}.json.

import json
import logging
import random
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from curl_cffi import requests

ROOT = Path(__file__).resolve().parents[4]
RAW_DIR = ROOT / "data" / "raw"

# How long after kickoff a match's data is taken as final
SETTLE = timedelta(hours=4)

log = logging.getLogger(__name__)


class Blocked(Exception):
    """The source answered 403 or 429. We stop rather than retry."""


def settled(kickoff: datetime, now: datetime | None = None) -> bool:
    """Whether a match's data can be taken as final."""
    return (now or datetime.now(UTC)) >= kickoff + SETTLE


def location(source: str, path: str) -> Path:
    return RAW_DIR / source / f"{path.strip('/')}.json"


def read(source: str, path: str) -> dict[str, Any]:
    """A saved record: {url, retrieved_at, status, body}."""
    record: dict[str, Any] = json.loads(location(source, path).read_text())
    return record


def http_get(url: str) -> tuple[int, str]:
    response = requests.get(url, impersonate="chrome", timeout=60)
    log.info("GET %s -> %d", url, response.status_code)
    return response.status_code, response.text


def request(url: str, *, delay: tuple[float, float]) -> dict[str, Any]:
    # Wait a random number of seconds between delay's two bounds
    time.sleep(random.uniform(*delay))

    # Impersonate Chrome, get the response, and return it as a record
    status, text = http_get(url)
    retrieved_at = datetime.now(UTC).isoformat()
    if status in (403, 429):
        raise Blocked(f"{url} returned {status}")
    if status not in (200, 404):
        raise RuntimeError(f"{url} returned {status}")
    try:
        body = json.loads(text)
    except ValueError:
        body = text
    return {"url": url, "retrieved_at": retrieved_at, "status": status, "body": body}


def save(source: str, path: str, record: dict[str, Any]) -> None:
    # Saved under RAW_DIR/{source}/{path}.json
    # Write then rename to prevent partial file corruption
    out = location(source, path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(record, indent=1, ensure_ascii=False))
    tmp.replace(out)


def fetch(
    source: str, path: str, url: str, *, delay: tuple[float, float] = (2, 5)
) -> Any:
    # If data exists already, get it
    out = location(source, path)
    if out.exists():
        log.info("skip %s: already saved", out)
        return read(source, path)["body"]

    # Else request it and save it
    record = request(url, delay=delay)
    save(source, path, record)
    return record["body"]
