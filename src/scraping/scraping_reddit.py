"""
Scrape r/Techno posts for a date range via the Arctic Shift archive API
(free Pushshift successor, no Reddit login or API key needed).

Output: one CSV row per post with
  post_date, artist, track, release_year, content_type (track/set),
  subgenre_flair, subgenre_keywords, mentioned_location, + raw fields.

Usage:
    pip install requests pandas
    python scrape_reddit_techno.py --after 2025-10-27 --before 2026-10-27
"""

import argparse
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import pandas as pd
import requests

API = "https://arctic-shift.photon-reddit.com/api/posts/search"
# Arctic Shift rejects unknown field names with HTTP 400 (domain/permalink are not allowed).
FIELDS = [
    "id", "created_utc", "title", "author", "link_flair_text", "url",
    "subreddit", "score", "num_comments", "selftext",
]

# ---------------------------------------------------------------- fetching

def fetch_posts(subreddit, after, before, page_size=100, pause=0.5):
    """Page through the archive in ascending time order."""
    rows, cursor = [], after
    session = requests.Session()
    while True:
        params = {
            "subreddit": subreddit,
            "after": cursor,
            "before": before,
            "limit": page_size,
            "sort": "asc",
            "fields": ",".join(FIELDS),
        }
        for attempt in range(5):
            r = session.get(API, params=params, timeout=60)
            if r.status_code == 200:
                break
            detail = r.text[:300]
            try:
                detail = r.json().get("error") or detail
            except ValueError:
                pass
            if r.status_code == 400:
                raise RuntimeError(f"HTTP 400 from API: {detail}")
            wait = 2 ** attempt * 5
            print(f"HTTP {r.status_code} ({detail}), retrying in {wait}s")
            time.sleep(wait)
        else:
            raise RuntimeError(f"Gave up at cursor {cursor}")

        batch = r.json().get("data", [])
        if not batch:
            break
        rows.extend(batch)
        last = batch[-1]["created_utc"]
        print(f"{len(rows):>6} posts, up to "
              f"{datetime.fromtimestamp(last, tz=timezone.utc):%Y-%m-%d}")
        if len(batch) < page_size:
            break
        cursor = int(last) + 1  # unix timestamp works as 'after'
        time.sleep(pause)

    # dedupe in case of overlapping timestamps
    return list({p["id"]: p for p in rows}.values())

# ---------------------------------------------------------------- parsing

SEP = re.compile(r"\s+[-–—]\s+")                  # "Artist - Track"
YEAR = re.compile(r"[\(\[]\s*((?:19[6-9]|20[0-2])\d)\s*[\)\]]")
YEAR_LOOSE = re.compile(r"\b((?:19[6-9]|20[0-2])\d)\b")
BRACKETS = re.compile(r"[\(\[].*?[\)\]]")

SET_WORDS = re.compile(
    r"\b(set|live at|live @|boiler ?room|b2b|mix|dj ?set|hör|cercle|"
    r"podcast|essential mix|recorded at)\b", re.I)

SUBGENRES = {
    "hard techno": r"hard ?techno",
    "industrial": r"industrial",
    "dub techno": r"dub ?techno",
    "minimal": r"minimal",
    "acid": r"\bacid\b",
    "detroit": r"detroit",
    "hypnotic": r"hypnotic",
    "melodic": r"melodic",
    "peak time": r"peak ?time",
    "schranz": r"schranz",
    "ambient techno": r"ambient",
    "hardgroove": r"hard ?groove",
    "raw/deep": r"\b(raw|deep) techno\b",
    "trance/rave": r"\b(trance|rave)\b",
    "ebm": r"\bebm\b",
}
SUBGENRE_RE = {k: re.compile(v, re.I) for k, v in SUBGENRES.items()}

# Rough location hints - noisy, meant as a starting point only.
# The more reliable route for country is joining artist -> Discogs.
LOCATIONS = [
    "Berlin", "Germany", "Detroit", "UK", "London", "Amsterdam",
    "Netherlands", "Belgium", "Brussels", "Paris", "France", "Tbilisi",
    "Georgia", "Italy", "Spain", "Barcelona", "Japan", "Tokyo",
    "Sweden", "Stockholm", "Denmark", "Copenhagen", "Poland", "Ukraine",
    "Kyiv", "Hungary", "Budapest", "Brazil", "Mexico", "Colombia",
    "Australia", "USA", "New York", "Chicago", "Canada", "Portugal",
]
LOC_RE = re.compile(r"\b(" + "|".join(map(re.escape, LOCATIONS)) + r")\b")


def link_domain(url):
    if not url:
        return None
    host = urlparse(url).netloc
    if not host:
        return None
    if host.endswith("reddit.com"):
        return "self." + (urlparse(url).path.split("/")[2] if "/r/" in url else "reddit")
    return host.removeprefix("www.")


def post_permalink(post):
    url = post.get("url") or ""
    if "reddit.com" in url and "/comments/" in url:
        path = urlparse(url).path
        return "https://reddit.com" + path if path else None
    pid = post.get("id")
    sub = post.get("subreddit")
    if pid and sub:
        return f"https://reddit.com/r/{sub}/comments/{pid}/"
    return None


def parse_title(title):
    out = {"artist": None, "track": None, "release_year": None}
    if not title:
        return out

    m = YEAR.search(title) or YEAR_LOOSE.search(title)
    if m:
        out["release_year"] = int(m.group(1))

    parts = SEP.split(title, maxsplit=1)
    if len(parts) == 2:
        artist, track = parts
        out["artist"] = BRACKETS.sub("", artist).strip(" |:") or None
        track = track.split("|")[0]          # drop "| genre" tails
        out["track"] = re.sub(r"\s+", " ", BRACKETS.sub("", track)).strip(" :") or None
    return out


def enrich(post):
    title = post.get("title") or ""
    flair = post.get("link_flair_text") or ""
    text = f"{title} {flair} {post.get('selftext') or ''}"

    row = {
        "post_id": post["id"],
        "post_date": datetime.fromtimestamp(
            post["created_utc"], tz=timezone.utc).date().isoformat(),
        "title": title,
        **parse_title(title),
        "content_type": "set" if SET_WORDS.search(title) else "track",
        "subgenre_flair": flair or None,
        "subgenre_keywords": ";".join(
            k for k, rx in SUBGENRE_RE.items() if rx.search(text)) or None,
        "mentioned_location": ";".join(
            sorted(set(LOC_RE.findall(text)))) or None,
        "domain": link_domain(post.get("url")),
        "url": post.get("url"),
        "score": post.get("score"),
        "num_comments": post.get("num_comments"),
        "author": post.get("author"),
        "permalink": post_permalink(post),
    }
    return row

# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subreddit", default="Techno")
    ap.add_argument("--after", default="2025-10-27")
    ap.add_argument("--before", default="2026-10-27")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    posts = fetch_posts(args.subreddit, args.after, args.before)
    df = pd.DataFrame([enrich(p) for p in posts]).sort_values("post_date")

    out = args.out or f"reddit_{args.subreddit.lower()}_{args.after}_{args.before}.csv"
    df.to_csv(out, index=False)

    print(f"\nSaved {len(df)} posts -> {out}")
    print(f"  artist parsed:       {df['artist'].notna().mean():.0%}")
    print(f"  release year parsed: {df['release_year'].notna().mean():.0%}")
    print(f"  has flair:           {df['subgenre_flair'].notna().mean():.0%}")
    print("\nTop flairs:\n", df["subgenre_flair"].value_counts().head(15))


if __name__ == "__main__":
    main()