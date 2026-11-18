# Annotation guide: how r/Techno talks about techno

**Research question:** How do people define techno and its subgenres, and where do they
draw the line between what is and isn't techno? The Reddit annotations complement the
Discogs data: Discogs shows how releases are *labelled*; Reddit shows how people *talk*.

## 1. What you annotate

- **Sample:** 50 r/Techno "Discussion" posts from 2025-10-27 to 2026-10-26
  (`annotations/sample_posts.csv`), drawn from three strata:
  - `popular`: the 20 highest-scoring posts
  - `genre_talk`: 20 heavily commented posts whose title or body talks about genres
  - `random`: 10 random posts, as a baseline
- **Unit:** one row in your sheet. Either the post itself (`unit_type = post`, title + body)
  or one of its 15 highest-scoring comments (`unit_type = comment`).
- **Your sheet:** `annotations/sheets/annotator_<n>.csv`. It has 10 posts that *everyone*
  annotates (used to measure agreement) plus about 13 posts that only you annotate.

| annotator | annotator # |
|---|---|
| Ivett | 1 |
| Michaela | 2 |
| Tobias | 3 |

Read `parent_text` for context (what the comment replies to). If you need more, open
`permalink`, e.g. when the post is an image or a video. **Code only what the unit itself says;**
don't code views that appear only in the parent or the thread.

## 2. The annotator tool

**Start it:** in the project folder, double-click **`annotate.command`** (Mac) or
**`annotate.bat`** (Windows) and type your annotator number, or give it in a terminal
(`2`, `annotator-2` or `annotator_2`):

```bash
./annotate.command 2        # Mac / Linux
annotate.bat 2              # Windows
```

It fetches the latest version (`git pull`), starts a small local server and opens the tool
in your browser **with your sheet already loaded**. **Save CSV** (<kbd>Ctrl/⌘ S</kbd>)
writes straight into `annotations/sheets/annotator_<n>.csv`, in any browser. Keep the
terminal window open while you work, and press <kbd>Ctrl+C</kbd> in it when you're done.
Each save keeps the previous version as `annotator_<n>.csv.bak` (not committed).

- Needs Python 3, which the project uses anyway; nothing extra to install.
- Mac, the first time: if macOS refuses to open it ("unidentified developer"), right-click
  `annotate.command` → **Open** → **Open**. After that, double-clicking works.
- Without the scripts (or without Python): open `annotations/annotator.html` in Chrome or
  Edge and pick your sheet by hand. Other browsers then download a copy on save, which you
  move over the original.

- Click the chips or use the keys: <kbd>Y</kbd>/<kbd>N</kbd> music-relevant;
  <kbd>I</kbd> <kbd>X</kbd> <kbd>C</kbd> <kbd>O</kbd> include / exclude / contested / none;
  <kbd>1</kbd>–<kbd>0</kbd> criteria; <kbd>P</kbd> <kbd>M</kbd> <kbd>B</kbd> <kbd>U</kbd>
  positive / negative / mixed / neutral; <kbd>A</kbd> add all artists found;
  <kbd>←</kbd> <kbd>→</kbd> move;
  <kbd>J</kbd> jump to the next uncoded unit; <kbd>Ctrl/⌘ S</kbd> save.
- A unit counts as done once "says anything about the music" is set. The left column shows
  progress per post.
- **Pre-tagged sheets:** units filled in by a model (column `pretagged`) show an orange
  banner and count as done only after you check them. Fix anything wrong, then press
  <kbd>V</kbd> ("Looks right"); editing a code also marks the unit as checked. The model's
  original tags stay in `annotations/pretags/` so we can report how often we changed them.
  Shared (agreement) posts are never pre-tagged, so the agreement score isn't skewed toward
  the model's choices.
- Edits are backed up in the browser as you go, and the tool offers to restore them if you
  close it without saving. **Save regularly anyway, and commit your sheet:** only the CSV counts.

## 3. Procedure

1. **Pilot first.** All three of us code the same 2 shared posts, then meet and compare.
   Write down every disagreement and the rule that settles it in §6 (Decision log).
2. Code the remaining shared posts **independently**: don't discuss them until all three are done.
3. Code your own posts.
4. Fill in the columns in order. If `genre_relevant = 0`, leave the other code columns empty
   (except `notes` if useful).
5. Don't edit or reorder the unit columns. Save as **CSV UTF-8**. In Excel, use
   "CSV UTF-8 (Comma delimited)", otherwise emojis and accents break.
6. For multi-value columns, separate values with `;` and no spaces, e.g. `tempo;sound`.

## 4. Codes

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

## 5. Agreement

The 10 shared posts (160 units) are coded by all three annotators. We report
**Krippendorff's alpha** per code (it handles 3 annotators and missing values): nominal for
`genre_relevant`, `boundary` and `stance`, and per-category binary for `criteria`. After
measuring agreement we resolve disagreements by discussion into one gold version of the
shared posts, recording the decisions in §6.

## 6. Decision log

Add rules here as they come up in the pilot and during coding:

| Date | Case | Decision |
|---|---|---|
| | | |

## 7. Known limitations of the sample

- Scores and comment counts come from the Arctic Shift archive, which captures each item
  ~36 hours after it is posted. They reflect early popularity, not final popularity.
- Only the top 15 comments per post (by that score) are annotated, so deeper sub-threads
  are under-represented.
- Only "Discussion"-flaired posts with at least 10 comments are in the sampling frame,
  so Track and Mix posts are not covered.
