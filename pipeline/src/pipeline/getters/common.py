# fetch() requests the URL with Chrome impersonation,
# and saves the response to data/raw/{source}/{path}.json
# as {url, retrieved_at, status, body}.

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from curl_cffi import requests

ROOT = Path(__file__).resolve().parents[4]
RAW_DIR = ROOT / "data" / "raw"

log = logging.getLogger(__name__)


class Blocked(Exception):
    """The source answered 403 or 429. We stop rather than retry."""


def http_get(url: str) -> tuple[int, str]:
    response = requests.get(url, impersonate="chrome", timeout=60)
    log.info("GET %s -> %d", url, response.status_code)
    return response.status_code, response.text


def fetch(source: str, path: str, url: str) -> Any:
    # If data exists already, get it
    out = RAW_DIR / source / f"{path.strip('/')}.json"
    if out.exists():
        log.info("skip %s: already saved", out)
        return json.loads(out.read_text())["body"]

    # Impersonate Chrome, get the response, and return the body
    status, text = http_get(url)
    retrieved_at = datetime.now(UTC).isoformat()
    if status in (403, 429):
        raise Blocked(f"{url} returned {status}")
    if status not in (200, 404):
        raise RuntimeError(f"{url} returned {status}")

    # Saved under RAW_DIR/{source}/{path}.json
    # Write then rename to prevent partial file corruption
    try:
        body = json.loads(text)
    except ValueError:
        body = text
    record = {"url": url, "retrieved_at": retrieved_at, "status": status, "body": body}
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(record, indent=1, ensure_ascii=False))
    tmp.replace(out)
    return body
