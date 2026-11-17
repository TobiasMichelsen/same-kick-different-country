# Step 1: pick the posts we annotate and split them between the annotators
#
# Only "Discussion" posts that weren't removed and have at least 10 comments.
# 3 groups (strata):
#   popular    - highest score (from the feedback)
#   genre_talk - most commented posts that talk about genre / subgenres
#   random     - random posts from the rest, as a baseline
#
# Who gets what:
#   all         - every annotator codes these (for the agreement)
#   annotator_N - only that annotator codes these
#   claude      - the rest, Claude does these later
#
# Output: annotations/sample_posts.csv
# Run from the repo root: python src/02_annotation/01_sample_posts.py

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
POSTS = ROOT / "data" / "processed" / "reddit_techno_posts.csv"
RAW_POSTS = ROOT / "data" / "raw" / "reddit" / "posts_techno_2025-10-27_2026-10-27.jsonl"
OUT = ROOT / "annotations" / "sample_posts.csv"

sys.path.insert(0, str(ROOT / "src" / "01_scraping"))
from scraping_reddit import SUBGENRES 

GENRE_TALK = re.compile(
    r"\b(?:genres?|sub-?genres?|styles?|bpm|tempo|kicks?|sound(?:s|ed)? like|"
    r"not (?:real )?techno|real techno|is (?:this|it) (?:even )?techno|"
    r"what (?:is|counts as) techno|defin\w*|gatekeep\w*|purists?|commerciali[sz]\w*|"
    r"underground|mainstream|revival|"
    + "|".join(f"(?:{p})" for p in SUBGENRES.values()) + r")\b", re.I)


# genre words found in a text
def genre_hits(text):
    return {m.group(0).lower() for m in GENRE_TALK.finditer(text or "")}


def load_frame(min_comments):
    df = pd.read_csv(POSTS)
    raw = pd.read_json(RAW_POSTS, lines=True)[["id", "selftext"]]
    df = df.merge(raw.rename(columns={"id": "post_id"}), on="post_id", how="left")
    frame = df[(df["subgenre_flair"] == "Discussion")
               & ~df["removed"]
               & ~df["stickied"]
               & (df["num_comments"] >= min_comments)].copy()
    # genre talk = genre word in the title, or 2+ different ones in the body
    # (one random mention in a long post is usually not about genre)
    title_hits = frame["title"].map(genre_hits)
    body_hits = frame["selftext"].map(genre_hits)
    frame["genre_terms"] = [";".join(sorted(t | b)) or None for t, b in zip(title_hits, body_hits)]
    frame["genre_talk"] = (title_hits.str.len() > 0) | (body_hits.str.len() >= 2)
    return frame


# most commented genre posts, max per_subgenre posts for the same subgenre
def pick_genre_talk(frame, n, per_subgenre):
    cand = frame[frame["genre_talk"]].sort_values("num_comments", ascending=False)
    counts, chosen = {}, []
    for _, row in cand.iterrows():
        key = (row["subgenre_keywords"] or "none").split(";")[0] \
            if isinstance(row["subgenre_keywords"], str) else "none"
        if key != "none" and counts.get(key, 0) >= per_subgenre:
            continue
        counts[key] = counts.get(key, 0) + 1
        chosen.append(row["post_id"])
        if len(chosen) == n:
            break
    return chosen


# how many of the n posts come from each stratum (same proportions as shares)
def stratum_quota(shares, n):
    exact = shares * n
    quota = exact.astype(int)
    for s in (exact - quota).sort_values(ascending=False).index[: n - quota.sum()]:
        quota[s] += 1
    return quota


# first the shared posts, then per_annotator posts for each annotator, the rest is claude
def assign(sample, annotators, overlap, per_annotator, rng):
    need = overlap + per_annotator * len(annotators)
    if need > len(sample):
        raise SystemExit(f"Need {need} posts but the sample has only {len(sample)}")
    sample = sample.sample(frac=1, random_state=rng).reset_index(drop=True)
    shares = sample["stratum"].value_counts(normalize=True)
    sample["assigned_to"] = None
    for label, n in [("all", overlap)] + [(a, per_annotator) for a in annotators]:
        free = sample[sample["assigned_to"].isna()]
        picked = [i for s, q in stratum_quota(shares, n).items()
                  for i in free[free["stratum"] == s].index[:q]]
        # if a stratum runs out, fill up from the others
        picked += [i for i in free.index if i not in picked][: n - len(picked)]
        sample.loc[picked, "assigned_to"] = label
    sample["assigned_to"] = sample["assigned_to"].fillna("claude")
    return sample


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--popular", type=int, default=20)
    ap.add_argument("--genre-talk", type=int, default=20)
    ap.add_argument("--random", type=int, default=10)
    ap.add_argument("--min-comments", type=int, default=10)
    ap.add_argument("--per-subgenre", type=int, default=3)
    ap.add_argument("--annotators", default="annotator_1,annotator_2,annotator_3")
    ap.add_argument("--overlap", type=int, default=10,
                    help="posts every annotator codes")
    ap.add_argument("--per-annotator", type=int, default=5,
                    help="posts only one annotator codes")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = np.random.RandomState(args.seed)

    frame = load_frame(args.min_comments)

    popular = frame.nlargest(args.popular, "score")["post_id"].tolist()
    rest = frame[~frame["post_id"].isin(popular)]
    genre = pick_genre_talk(rest, args.genre_talk, args.per_subgenre)
    rest = rest[~rest["post_id"].isin(genre)]
    rand = rest.sample(args.random, random_state=rng)["post_id"].tolist()

    strata = {**{p: "popular" for p in popular},
              **{p: "genre_talk" for p in genre},
              **{p: "random" for p in rand}}
    sample = frame[frame["post_id"].isin(strata)].copy()
    sample["stratum"] = sample["post_id"].map(strata)
    sample = assign(sample, args.annotators.split(","), args.overlap,
                    args.per_annotator, rng)

    cols = ["post_id", "stratum", "assigned_to", "title", "post_date", "score",
            "num_comments", "subgenre_keywords", "genre_terms", "genre_talk", "permalink"]
    sample = sample.sort_values(["stratum", "score"], ascending=[True, False])[cols]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(OUT, index=False)

    print(f"Frame: {len(frame)} Discussion posts with >= {args.min_comments} comments")
    print(f"Saved {len(sample)} posts -> {OUT.relative_to(ROOT)}\n")
    print(pd.crosstab(sample["stratum"], sample["assigned_to"], margins=True))


if __name__ == "__main__":
    main()
