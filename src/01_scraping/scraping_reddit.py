"""
Scrape subreddit posts for a date range via the Arctic Shift archive API
and turn them into a tidy CSV.

Two stages, so the parser can change without re-scraping:
  1. fetch  -> data/raw/reddit/posts_<sub>_<after>_<before>.jsonl  (full API records)
  2. parse  -> data/processed/reddit_<sub>_posts.csv               (one row per post)

Usage (from the repo root):
    python src/01_scraping/scraping_reddit.py --after 2025-10-27 --before 2026-10-27
    python src/01_scraping/scraping_reddit.py --refetch      # ignore cached raw file
"""

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

import arctic_shift

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "reddit"
OUT_DIR = ROOT / "data" / "processed"

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
LOCATIONS = [
    "Berlin", "Germany", "Detroit", "UK", "London", "Amsterdam",
    "Netherlands", "Belgium", "Brussels", "Paris", "France", "Tbilisi",
    "Georgia", "Italy", "Spain", "Barcelona", "Japan", "Tokyo",
    "Sweden", "Stockholm", "Denmark", "Copenhagen", "Poland", "Ukraine",
    "Kyiv", "Hungary", "Budapest", "Brazil", "Mexico", "Colombia",
    "Australia", "USA", "New York", "Chicago", "Canada", "Portugal",
]
LOC_RE = re.compile(r"\b(" + "|".join(map(re.escape, LOCATIONS)) + r")\b")

REMOVED = {"moderator", "reddit", "deleted", "content_takedown"}


def link_domain(url):
    if not url:
        return None
    host = urlparse(url).netloc
    if not host:
        return None
    if host.endswith("reddit.com"):
        return "self." + (urlparse(url).path.split("/")[2] if "/r/" in url else "reddit")
    return host.removeprefix("www.")


def parse_title(title):
    out = {"artist": None, "track": None, "release_year": None}
    if not title:
        return out

    m = YEAR.search(title) or YEAR_LOOSE.search(title)
    if m:
        out["release_year"] = int(m.group(1))

    # drop bracketed bits first so "(1962 - 2026)" is not read as a separator
    parts = SEP.split(BRACKETS.sub("", title), maxsplit=1)
    if len(parts) == 2:
        artist, track = parts
        out["artist"] = artist.strip(" |:") or None
        track = track.split("|")[0]          # drop "| genre" tails
        out["track"] = re.sub(r"\s+", " ", track).strip(" :–-") or None
    return out


def enrich(post):
    title = post.get("title") or ""
    flair = post.get("link_flair_text") or ""
    text = f"{title} {flair} {post.get('selftext') or ''}"
    meta = post.get("_meta") or {}

    return {
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
        "is_self": post.get("is_self"),
        "selftext_len": len(post.get("selftext") or ""),
        "score": post.get("score"),
        "upvote_ratio": post.get("upvote_ratio"),
        "num_comments": post.get("num_comments"),
        "stickied": post.get("stickied"),
        # 'automod_filtered' is the state at first capture (held for review) and
        # many such posts were approved later, so it does not count as removed.
        "removed_by_category": post.get("removed_by_category"),
        "removed": post.get("removed_by_category") in REMOVED,
        "author": post.get("author"),
        "permalink": f"https://reddit.com/r/{post.get('subreddit')}/comments/{post['id']}/",
        "score_retrieved_on": datetime.fromtimestamp(
            meta.get("retrieved_2nd_on") or post.get("retrieved_on") or 0,
            tz=timezone.utc).isoformat(timespec="seconds"),
    }

# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subreddit", default="Techno")
    ap.add_argument("--after", default="2025-10-27")
    ap.add_argument("--before", default="2026-10-27")
    ap.add_argument("--refetch", action="store_true", help="ignore cached raw file")
    args = ap.parse_args()

    sub = args.subreddit.lower()
    raw = RAW_DIR / f"posts_{sub}_{args.after}_{args.before}.jsonl"
    if raw.exists() and not args.refetch:
        print(f"Using cached {raw.relative_to(ROOT)}")
        posts = arctic_shift.read_jsonl(raw)
    else:
        posts = arctic_shift.fetch_posts(args.subreddit, args.after, args.before)
        arctic_shift.write_jsonl(posts, raw)
        print(f"Saved {len(posts)} raw posts -> {raw.relative_to(ROOT)}")

    df = pd.DataFrame([enrich(p) for p in posts]).sort_values("post_date")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"reddit_{sub}_posts.csv"
    df.to_csv(out, index=False)

    tracks = df[df["subgenre_flair"] == "Track"]
    print(f"\nSaved {len(df)} posts -> {out.relative_to(ROOT)}")
    print(f"  artist parsed (Track flair): {tracks['artist'].notna().mean():.0%}")
    print(f"  release year parsed:         {df['release_year'].notna().mean():.0%}")
    print(f"  has flair:                   {df['subgenre_flair'].notna().mean():.0%}")
    print("\nFlairs:\n", df["subgenre_flair"].value_counts().head(15))


if __name__ == "__main__":
    main()
