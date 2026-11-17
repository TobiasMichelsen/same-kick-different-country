"""
Minimal client for the Arctic Shift Reddit archive API
(https://arctic-shift.photon-reddit.com), a free Pushshift successor.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://arctic-shift.photon-reddit.com/api"
PAGE_SIZE = 100

_session = requests.Session()
_session.headers["User-Agent"] = "same-kick-different-country research script"


def get(endpoint, params, pause=0.5):
    """GET with retries; returns the `data` list."""
    for attempt in range(5):
        r = _session.get(f"{API}/{endpoint}", params=params, timeout=60)
        if r.status_code == 200:
            time.sleep(pause)
            return r.json().get("data") or []
        detail = r.text[:300]
        try:
            detail = r.json().get("error") or detail
        except ValueError:
            pass
        if r.status_code == 400:
            raise RuntimeError(f"HTTP 400 from {endpoint}: {detail}")
        wait = 2 ** attempt * 5
        print(f"HTTP {r.status_code} ({detail}), retrying in {wait}s")
        time.sleep(wait)
    raise RuntimeError(f"Gave up on {endpoint} {params}")


def _paginate(endpoint, params, label=""):
    """Page through a search endpoint in ascending time order, deduped by id."""
    seen, cursor = {}, params.get("after")
    while True:
        batch = get(endpoint, {**params, "after": cursor, "limit": PAGE_SIZE, "sort": "asc"})
        new = [x for x in batch if x["id"] not in seen]
        for x in new:
            seen[x["id"]] = x
        if label and new:
            last = datetime.fromtimestamp(batch[-1]["created_utc"], tz=timezone.utc)
            print(f"{label}{len(seen):>6} items, up to {last:%Y-%m-%d}")
        if len(batch) < PAGE_SIZE or not new:
            break
        cursor = int(batch[-1]["created_utc"])
    return list(seen.values())


def fetch_posts(subreddit, after, before):
    """All posts in a subreddit between two dates (YYYY-MM-DD), all fields."""
    return _paginate("posts/search",
                     {"subreddit": subreddit, "after": after, "before": before},
                     label="posts ")


def fetch_comments(post_id):
    """All archived comments of one post, all fields (flat; use parent_id for the tree)."""
    return _paginate("comments/search", {"link_id": post_id})


def write_jsonl(items, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for x in items:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
