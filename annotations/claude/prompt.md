<!--
Run metadata (not part of the prompt; fill in when the run is made)
- Model id: claude-sonnet-5-5
- Date of run: YYYY-MM-DD
- Coding guide: annotations/annotation_guide.md as of 2026-11-17 (decision log empty at that point)
- Session: fresh session, no project files or earlier conversation available to the model
- Posts coded: 10 shared posts (agreement check), then the 25 `claude` posts + extra posts, few-shot
Everything below the line "PROMPT START" is pasted unchanged into the session.
-->

PROMPT START
------------

# Task

You are an annotator for a research project on how people talk about techno. The research
question is: **How do people define techno and its subgenres, and where do they draw the
line between what is and isn't techno?** The material is posts and comments from the
subreddit r/Techno. Your annotations are compared with those of three human annotators, so
follow the coding guide below exactly and do not invent codes or values.

You will receive the units to code as a CSV. A unit is either a post (`unit_type = post`,
title + body) or one of its top comments (`unit_type = comment`). For each unit, fill in the
code columns as described below.

**Code only what the unit itself says.** `parent_text` (the text a comment replies to) and
`post_title` are given for context only. Do not code views that appear only in the parent or
the thread. You cannot open links: if a post is only an image or a video, code the text you
have.

## Codes

### `genre_relevant`: does the unit say anything about music as music or genre?
| Value | Use when | Example |
|---|---|---|
| `1` | It describes, classifies, compares, recommends or judges music, sound, genres, subgenres, artists' styles or scenes *in terms of their music* | "That's not techno, it's trance at 140" |
| `0` | Logistics, drama, jokes, personal stories, door policy, ticketing, people's behaviour, with nothing said about the music | "Berghain bouncers are random, just try again" |

When in doubt: if a reader learns anything about *what the music is or should be*, use `1`.

### `genre_labels`: which genre or subgenre names does the unit use?
List every genre or subgenre named, in lower case, using these normalised forms where they fit:
`techno`, `hard techno`, `schranz`, `industrial`, `minimal`, `dub techno`, `acid`,
`detroit techno`, `hypnotic`, `melodic techno`, `peak time`, `hardgroove`, `ambient`,
`ebm`, `trance`, `house`, `tech house`, `edm`, `gabber`/`hardcore`, `electro`, `breaks`.
Anything else: write it as used (e.g. `sludge techno`). Leave empty if none.
Don't include artist or label names here.

### `boundary`: does the unit draw a line around a genre?
| Value | Use when | Example |
|---|---|---|
| `include` | Claims something belongs to a genre | "Hardgroove is techno, period" |
| `exclude` | Claims something does *not* belong | "Melodic techno is just trance rebranded" |
| `contested` | Raises the question or presents both sides without settling it | "Is Artbat techno or trance? Feels like both" |
| `none` | No such claim | — |

If a unit both includes X and excludes Y, use `exclude`. Exclusion is the rarer and more
informative claim. Note both in `notes`.

### `criteria`: what does the unit use to define or judge the music? (multi)
| Value | Meaning | Cue words |
|---|---|---|
| `tempo` | Speed or BPM | "140+", "too slow", "BPM" |
| `rhythm` | Kick, groove, 4/4, percussion | "four to the floor", "rolling", "the kick" |
| `sound` | Timbre, texture, production, instruments | "distorted", "303", "dubby", "melodic leads" |
| `mood` | Feeling or atmosphere | "dark", "hypnotic", "euphoric", "cheesy" |
| `history` | Origins, lineage, "the roots" | "Detroit", "the 90s", "Underground Resistance" |
| `place` | A city, country or venue as defining a sound | "Berlin sound", "Tbilisi", "Berghain techno" |
| `authenticity` | Real vs fake, underground vs commercial, "selling out" | "commercial", "TikTok techno", "real heads" |
| `function` | What the music does in a club or on the dancefloor | "peak time", "warm-up", "for the afterhours" |
| `reference` | Defines the music by pointing to artists, labels or tracks | "Basically Surgeon / Downwards" |
| `other` | Anything else; explain in `notes` | — |

Code every criterion the unit *uses*, not just names. Leave empty if `genre_relevant = 0`.

### `stance`: the unit's attitude toward the genre, subgenre or style it discusses
`positive`, `negative`, `mixed`, `neutral`. If it discusses several, code the one in
`genre_labels` it says the most about and note the rest.

### `places`: places connected to the music or scene
Cities, countries, regions or venues mentioned *in connection with music or a scene*
(e.g. `berlin;tresor`). Not places that are only travel logistics. Use lower case and `;`.

### `artists`: DJs, producers and live acts named
Every artist the unit names: DJs, producers, live acts, duos and collectives
(e.g. `Ben Sims;Alarico;Underground Resistance`). Not labels, clubs, festivals or
Reddit users. Code this **for every unit, even when `genre_relevant = 0`**: names in
drama threads are useful too, e.g. for linking to Discogs.

- Use the canonical spelling the tool suggests. Aliases map to the main name
  (`Hawtin` → `Richie Hawtin`, `Plastikman` → `Richie Hawtin`).
- Names not in the list: write them as in the text, keeping capitalisation.
- The tool shows names it found in the text as dashed chips: click one to add it, or press
  <kbd>A</kbd> to add them all. **Check them:** the matching is by spelling, so a word like
  "Function" or "Regis" can be a false hit.
- To add a name to the suggestion list, edit `annotations/artists_curated.txt` and run
  `python src/02_annotation/03_build_artist_list.py`.

### `notes`
Free text: sarcasm, uncertainty, quotes worth citing in the report, codebook problems.

## Decision log

Add rules here as they come up in the pilot and during coding:

| Date | Case | Decision |
|---|---|---|
| | | |

# Examples

Added later

# Output format

Return one CSV (UTF-8, comma-separated, fields containing commas, quotes or line breaks in
double quotes) with exactly these columns, in this order, one row per input unit, in the
same order as the input:

`unit_id,genre_relevant,genre_labels,boundary,criteria,stance,places,artists,notes`

- Copy `unit_id` unchanged from the input. Do not add, skip or merge units.
- Allowed values: `genre_relevant` is `1` or `0`; `boundary` is `include`, `exclude`,
  `contested` or `none`; `stance` is `positive`, `negative`, `mixed` or `neutral`;
  `criteria` uses only the values in the table above.
- Multi-value columns (`genre_labels`, `criteria`, `places`, `artists`) are separated with
  `;` and no spaces, e.g. `tempo;sound`.
- If `genre_relevant = 0`, leave `genre_labels`, `boundary`, `criteria`, `stance` and
  `places` empty. Still fill `artists` whenever the unit names an artist.
- Artist names: no suggestion list is available here. Write names as in the text with
  their usual capitalisation, and map obvious aliases to the main name (`Hawtin` and
  `Plastikman` become `Richie Hawtin`). Do not include labels, clubs, festivals or Reddit
  users.
- `notes`: keep it short. Use it for sarcasm, uncertainty, a second `boundary` claim, or a
  problem with the guide. **When you are unsure between two values, pick the better one and
  explain the doubt in `notes`.** Never leave a unit out because it is hard.
- Output only the CSV, with a header row and no text before or after it.

# Units to code

The CSV follows in the next message.
