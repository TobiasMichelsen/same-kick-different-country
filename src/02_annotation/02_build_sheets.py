# Step 2: get the comments for the sampled posts and make the annotation sheets
#
# A unit = the post (title + text) or one of its top 15 comments (by score).
# Deleted comments and bots are left out. Every comment also gets the text it
# replies to (parent_text), so you can read it in context.
#
# Input:  annotations/sample_posts.csv (from step 1)
# Output: annotations/units.csv and annotations/sheets/annotator_N.csv
# Comments are saved in data/raw/reddit/comments/ so we only download them once.
#
# Existing sheets are NOT overwritten (so we don't lose work), use --force for that.
# Run from the repo root: python src/02_annotation/02_build_sheets.py

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "01_scraping"))
import arctic_shift  # noqa: E402

SAMPLE = ROOT / "annotations" / "sample_posts.csv"
RAW_POSTS = ROOT / "data" / "raw" / "reddit" / "posts_techno_2025-10-27_2026-10-27.jsonl"
COMMENT_DIR = ROOT / "data" / "raw" / "reddit" / "comments"
UNITS = ROOT / "annotations" / "units.csv"
SHEET_DIR = ROOT / "annotations" / "sheets"
CLAUDE_DIR = ROOT / "annotations" / "claude"


GONE = {"[deleted]", "[removed]", ""}
BOTS = {"AutoModerator"}
CODE_COLUMNS = ["genre_relevant", "genre_labels", "boundary", "criteria",
                "stance", "places", "artists", "notes"]
CONTEXT_CHARS = 300


# comments of a post, from the saved file or downloaded
def comments_for(post_id):
    path = COMMENT_DIR / f"{post_id}.jsonl"
    if path.exists():
        return arctic_shift.read_jsonl(path)
    comments = arctic_shift.fetch_comments(post_id)
    arctic_shift.write_jsonl(comments, path)
    print(f"  {post_id}: {len(comments)} comments")
    return comments


# shorten the parent text
def clip(text, n=CONTEXT_CHARS):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n] + "…"


# the post + its top_k comments as rows
def units_for(post, comments, top_k):
    pid = post["id"]
    base = f"https://reddit.com/r/{post['subreddit']}/comments/{pid}/"
    rows = [{
        "unit_id": f"p_{pid}", "post_id": pid, "unit_type": "post",
        "author": post.get("author"), "score": post.get("score"),
        "parent_text": None,
        "text": " ".join(filter(None, [post.get("title"), post.get("selftext")])),
        "permalink": base,
    }]

    by_id = {c["id"]: c for c in comments}
    keep = [c for c in comments
            if (c.get("body") or "").strip() not in GONE and c.get("author") not in BOTS]
    keep.sort(key=lambda c: c.get("score") or 0, reverse=True)
    for c in keep[:top_k]:
        parent_id = (c.get("parent_id") or "")
        if parent_id.startswith("t3_"):
            parent = "[post] " + (post.get("title") or "")
        else:
            parent = (by_id.get(parent_id[3:]) or {}).get("body", "[parent not archived]")
        rows.append({
            "unit_id": f"c_{c['id']}", "post_id": pid, "unit_type": "comment",
            "author": c.get("author"), "score": c.get("score"),
            "parent_text": clip(parent), "text": c.get("body"),
            "permalink": f"{base}_/{c['id']}/",
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-k", type=int, default=15, help="comments per post")
    ap.add_argument("--force", action="store_true", help="overwrite existing sheets")
    args = ap.parse_args()

    sample = pd.read_csv(SAMPLE)
    posts = {p["id"]: p for p in arctic_shift.read_jsonl(RAW_POSTS)
             if p["id"] in set(sample["post_id"])}

    print(f"Comments for {len(sample)} posts (cached in {COMMENT_DIR.relative_to(ROOT)})")
    rows = []
    for _, s in sample.iterrows():
        post = posts[s["post_id"]]
        for u in units_for(post, comments_for(s["post_id"]), args.top_k):
            rows.append({"stratum": s["stratum"], "assigned_to": s["assigned_to"],
                         "post_title": post.get("title"), **u})

    units = pd.DataFrame(rows)
    units.to_csv(UNITS, index=False, encoding="utf-8-sig")
    print(f"\nSaved {len(units)} units -> {UNITS.relative_to(ROOT)}")

    SHEET_DIR.mkdir(parents=True, exist_ok=True)
    # 'all' posts go in every human sheet, claude gets them in a separate file (blind test)
    humans = sorted(a for a in sample["assigned_to"].unique() if a.startswith("annotator_"))
    sheets = {SHEET_DIR / f"{a}.csv": [a, "all"] for a in humans}
    sheets[CLAUDE_DIR / "claude_zeroshot.csv"] = ["all"]
    sheets[CLAUDE_DIR / "claude.csv"] = ["claude"]
    cols = ["unit_id", "post_id", "stratum", "unit_type", "post_title", "parent_text",
            "text", "score", "permalink"]
    for path, groups in sheets.items():
        sheet = units[units["assigned_to"].isin(groups)][cols].copy()
        for c in CODE_COLUMNS:
            sheet[c] = ""
        if path.exists() and not args.force:
            print(f"  {path.relative_to(ROOT)} exists, not overwritten ({len(sheet)} units)")
            continue
        sheet.to_csv(path, index=False, encoding="utf-8-sig")
        n_posts = sheet["post_id"].nunique()
        print(f"  {path.relative_to(ROOT)}: {n_posts} posts, {len(sheet)} units")


if __name__ == "__main__":
    main()
