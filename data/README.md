# Smart Resource Matcher — Person A: Data + Retrieval Pipeline

This is a **working, tested starting point** for your part of the project. Everything
in here runs. Your job now is mostly: (1) swap in real data for your city, (2) tune
quality, (3) hand `retrieve()` off to Person B.

---

## 0. What's actually in this folder

```
smart-resource-matcher/
├── data/
│   ├── resources.csv                   <- DEFAULT dataset all scripts use (198 rows)
│   ├── resources_real_houston.csv      <- 128 rows, ALL real & verified (100 HRSA health + 28 hand-researched)
│   ├── resources_hrsa_filtered.csv     <- just the 100 real HRSA health rows
│   ├── resources_real_researched.csv   <- just the 28 hand-researched real rows (food/shelter/legal/etc.)
│   ├── resources_placeholder_others.csv<- 98 placeholder rows (renamed, no longer real orgs)
│   └── resources_sample.csv            <- original 30-row synthetic "Rivertown" demo data
├── scripts/
│   ├── common.py                  <- shared helpers: CSV loading, distance, hours parsing
│   ├── retrieve_tfidf.py          <- QUICK-START retrieval (no internet needed) — WORKS NOW
│   ├── ingest_chroma.py           <- "real" pipeline: builds embeddings + Chroma index
│   ├── retrieve_chroma.py         <- "real" pipeline: retrieval using those embeddings
│   ├── geocode_helper.py          <- turns addresses into lat/lng using free OpenStreetMap API
│   ├── ingest_hrsa.py             <- turns the national HRSA CSV into our schema, filtered by city/state
│   ├── generate_placeholder_others.py  <- (re)generates placeholder rows if you want to tweak them
│   ├── rename_placeholders.py     <- strips "[SAMPLE]" and assigns varied names, keeps disclosure in description
│   └── api.py                     <- optional FastAPI wrapper for Person B
├── test_queries.py                <- Step 7: sanity-check search quality
├── example_result_handling.py     <- shows safe None-handling for distance_km / is_open_now
├── requirements.txt
└── README.md                      <- you are here
```

**`data/resources.csv` is what every script defaults to.** It's 198 rows: 100 real
HRSA-verified Houston health centers, plus 98 rows across food/shelter/legal/financial/
childcare/mental_health/other that have varied, non-`[SAMPLE]`-prefixed names but are
**still not real organizations** — their `description` field says so explicitly
("PLACEHOLDER ENTRY... replace with a real, verified local organization"). That
disclosure is left in on purpose: these rows have invented addresses and phone
numbers, and a tool like this could plausibly be used by someone in an actual crisis
("emergency shelter tonight"). Before any live demo in front of real users, swap these
98 rows for real ones — `data/resources_real_researched.csv` already has 28 fully real
replacements ready to use, and `scripts/ingest_hrsa.py` / manual curation (Step 2/3b
below) covers the rest.

---

## 1. Get VS Code set up (10 min)

1. **Install VS Code** if you don't have it: https://code.visualstudio.com/
2. **Install Python** if you don't have it (3.10+): https://www.python.org/downloads/
   - On Windows, check "Add Python to PATH" during install.
3. Open VS Code → **File → Open Folder** → select the `smart-resource-matcher` folder
   you downloaded from this chat.
4. Install the **Python extension**: click the Extensions icon in the left sidebar
   (or `Ctrl+Shift+X` / `Cmd+Shift+X`), search "Python", install the Microsoft one.
5. Open a terminal inside VS Code: **Terminal → New Terminal** (or `` Ctrl+` ``).
   Everything below is typed into that terminal.

### Create a virtual environment (keeps this project's packages separate from everything else on your machine)

```bash
# Mac/Linux:
python3 -m venv venv
source venv/bin/activate

# Windows:
python -m venv venv
venv\Scripts\activate
```

You'll know it worked because your terminal prompt will now start with `(venv)`.
**Do this every time you open a new terminal for this project** — if you don't see
`(venv)`, run the `source venv/bin/activate` (or Windows equivalent) line again.

In VS Code, you can also click the Python version in the bottom-right status bar and
select the `venv` interpreter, so the editor itself (not just the terminal) knows to
use it.

### Install dependencies

```bash
pip install -r requirements.txt
```

This installs everything for both the quick-start and the "real" pipeline. Takes 1-3 min.

---

## 2. Run the quick-start pipeline right now (2 min)

This uses TF-IDF (basically: word-overlap-based similarity) instead of a neural
embedding model, so it needs **zero internet access** and **zero API keys**. It's not
as smart as the "real" pipeline, but it proves everything is wired correctly before
you add complexity.

```bash
python test_queries.py
```

You should see ~15 queries each print their top 3 matching resources with a score.
I already ran this myself and it works — for example:

```
QUERY: mental health counseling sliding scale
   [0.5607] Hillcrest Mental Health Counseling  (mental_health)
   [0.3878] Rivertown Sliding Scale Therapy Collective  (mental_health)
   [0.3214] Rivertown Crisis Counseling Hotline  (mental_health)
```

**One thing worth noticing:** the query `"my electricity is about to get shut off"`
returns nothing good, because the actual resource is described using the word
"utility" instead of "electricity" — TF-IDF only matches on shared words, not
meaning. That's *exactly* the problem the sentence-transformers model in Step 5
below solves (it understands "electricity" and "utility" are related concepts).
Keep this in your back pocket — it's a great "here's why we upgraded" line for
judges if they ask about your architecture choices.

---

## 3. Step 2 from the original plan: get REAL data for your city (2-4 hrs)

Now replace the placeholder Rivertown data with real organizations.

1. Open `data/resources_sample.csv` in VS Code (or Excel/Google Sheets — a CSV opens
   fine in either) and use it as your template. Keep the exact same column headers.
2. Pick your city. Go to **211.org**, search your area, and start pulling in real
   entries — or check your city/county's health department, food bank locator, or
   open data portal if one exists.
3. Aim for 100-150 rows across all 8 categories (food, health, shelter, legal,
   financial, childcare, mental_health, other). Even 60-80 solid entries is fine
   for a demo if you're short on time — quality and variety matter more than count.
4. **The `description` field is the most important one** — it's what gets embedded
   and searched against. Write 2-3 real, specific sentences per resource (what they
   do, who it's for, any specifics like "no insurance needed" or "walk-ins welcome").
   Copy-pasting a one-line address as the description will make search quality bad.
5. Save your real file as `data/resources_real.csv` (keep `resources_sample.csv`
   around — useful for testing/fallback demos).

### Getting lat/lng for real addresses

If you have addresses but no coordinates, run:

```bash
python scripts/geocode_helper.py data/resources_real.csv
```

This uses the free OpenStreetMap/Nominatim geocoder (no API key needed) and writes
`data/resources_real_geocoded.csv` with lat/lng filled in. It respects the 1
request/second rate limit, so 150 rows takes ~2.5 minutes — let it run, don't
interrupt it.

Then just point the scripts at your new file (see Step 4/5 below — change
`CSV_PATH` / `csv_path`).

## 3b. Using the HRSA Health Center Service Delivery Sites dataset (real gov data)

**Yes, this dataset is usable** — it's public federal data (HRSA, Bureau of Primary
Health Care), and HRSA's own data-sources page lists "Usage limitations: None" for it.
No attribution or licensing hoops. It covers your `health` category with ~16,000 real,
verified clinics nationwide.

- CSV: https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites.csv
- Metadata (exact column definitions): https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites_Data_Download_Metadata.xlsx
- Main page (if the direct link ever changes): https://data.hrsa.gov/data/download

**Note:** I couldn't download this file myself to verify the exact column names — my
sandbox's network allowlist blocks `data.hrsa.gov`. That's a limitation of my
environment, not a problem with the file. `scripts/ingest_hrsa.py` (new) is built to
handle this: it has an `--inspect` mode that prints the real column headers from your
downloaded copy before processing anything, so you confirm the mapping yourself rather
than trusting a guess.

**Workflow:**
1. Download the CSV from the link above and save it as `data/raw_hrsa_sites.csv`.
2. Run `python scripts/ingest_hrsa.py --inspect` — check the printed column names
   against the metadata xlsx, and adjust `COLUMN_MAP` at the top of the script if
   anything differs from what's there.
3. Run `python scripts/ingest_hrsa.py --state TX --city Austin` (swap in your state/city)
   to filter the ~16,000 national rows down to something demo-sized. This writes
   `data/resources_hrsa_filtered.csv` in our schema.
4. It auto-generates the `description` field (HRSA's file doesn't have one) using a
   template that includes the actual site type where available — e.g. "Federally
   supported community health center offering primary care services... Site type:
   Federally Qualified Health Center Look-Alike."
5. **`hours` gets set to a placeholder** ("Call to confirm hours") since this dataset
   has no structured open/close times. This is safe — `open_now()` already returns
   `None` (not `False`) for unparseable hours, so these sites won't be wrongly shown
   as closed (see section 9a above). Backfill real hours manually for your highest-
   priority sites if you have time.
6. Concatenate the output with your manually curated rows for the other categories:
   ```python
   import pandas as pd
   hrsa = pd.read_csv("data/resources_hrsa_filtered.csv")
   other = pd.read_csv("data/resources_other_categories.csv")  # your shelter/legal/financial/childcare entries
   combined = pd.concat([hrsa, other], ignore_index=True)
   combined.to_csv("data/resources_real.csv", index=False)
   ```
7. You still need **10-20 manually curated entries** for shelter, legal, financial,
   and childcare — HRSA only covers health. This is unavoidable manual work; there's
   no equivalent single federal source covering all four categories, so budget the
   time in Step 2's 2-4 hour window accordingly.



Once your real data is ready (or even now, to test with the sample data), build the
actual vector index:

```bash
python scripts/ingest_chroma.py
```

First run downloads a small (~80MB) embedding model — needs internet just this once.
It'll print progress, then say something like:

```
Done. Indexed 30 resources into collection 'resources'.
```

This creates a `chroma_db/` folder in your project — that's your local vector database.

To use your real data instead of the sample, open `scripts/ingest_chroma.py` and change:
```python
CSV_PATH = "data/resources_sample.csv"
```
to
```python
CSV_PATH = "data/resources_real_geocoded.csv"
```
then re-run `python scripts/ingest_chroma.py`. **Re-run this any time your CSV
changes** — it rebuilds the whole index from scratch.

### Test the real retrieval:

```bash
python scripts/retrieve_chroma.py
```

Compare its output to `retrieve_tfidf.py`'s output on the same queries — you should
see noticeably better matches, especially on queries that don't share exact words
with the descriptions (like the electricity/utility example above).

---

## 5. The function contract Person B depends on

Both `retrieve_tfidf.py` and `retrieve_chroma.py` expose the same shape, so whichever
one you hand off, Person B's code doesn't need to change:

```python
from retrieve_tfidf import TfidfResourceIndex   # or: from retrieve_chroma import ChromaResourceIndex

index = TfidfResourceIndex()   # loads data + builds index once

results = index.retrieve(
    query="I need free dental care for my kid, no insurance",
    top_k=5,
    category=None,              # or e.g. "health" to filter
    user_lat=30.27, user_lng=-97.74,   # optional
    max_distance_km=10,         # optional
    require_open_now=False,    # optional
)
```

Returns a list of dicts, best match first:

```python
{
  "id": 1, "name": "...", "category": "...", "description": "...",
  "eligibility": "...", "address": "...", "hours": "...", "phone": "...",
  "website": "...", "walk_in": True, "last_verified": "2026-06-01",
  "score": 0.34,            # higher = better match
  "distance_km": 2.3,       # None if no user location given
  "is_open_now": True,      # True / False / None (None = couldn't parse hours)
}
```

**Send Person B this section** (or the whole README) plus your GitHub link — this is
the contract they'll build their prompt/frontend code against.

---

## 6. Optional: expose it as an HTTP API instead

If Person B prefers calling your pipeline over HTTP rather than importing it as a
Python function:

```bash
cd scripts
uvicorn api:app --reload --port 8000
```

Then in a browser or with `curl`:
```
http://127.0.0.1:8000/retrieve?query=free dental care for my kid&top_k=3
```

Flip `USE_CHROMA = True` at the top of `scripts/api.py` once your Chroma index is
built and you want the smarter backend live.

---

## 7. Step 7 from the plan: test quality, and what to do if results look bad

Run (or re-run) the quality check any time you change data or switch backends:

```bash
python test_queries.py
```

If a query returns bad or empty results, in order of likely cause:
1. **The resource's description is too thin.** Add more descriptive, plain-language
   detail — mention specific situations someone might describe ("no insurance",
   "walk-ins welcome", "sliding scale", "24/7", "for families with children").
2. **top_k is too small.** Bump it up temporarily to see if the right resource is
   just barely missing the cutoff.
3. **You're still on TF-IDF and the vocabulary doesn't overlap** (see the
   electricity/utility example). Switch to `retrieve_chroma.py` — semantic
   embeddings solve most of this class of problem automatically.

---

## 8. Push to GitHub early (30 min)

Don't wait until this is "done" — Person B needs to start integrating ASAP.

```bash
git init
git add .
git commit -m "Person A: data + retrieval pipeline v1"
git remote add origin <your shared repo URL>
git push -u origin main
```

If `venv/` or `chroma_db/` accidentally got committed, add a `.gitignore`:
```
venv/
chroma_db/
__pycache__/
*.pyc
```

---

## 9. Notes from the last review — read before handing off to Person B

Three things came up that are worth locking down explicitly:

### a) `distance_km` and `is_open_now` can be `None` — handle that gracefully
`is_open_now` is **tri-state**: `True`, `False`, or `None` (hours couldn't be
confidently parsed, e.g. `"Rotating - 1st Sat monthly"`). `None` must never be
treated as "closed" — collapsing it to False would incorrectly hide or badmouth
a resource that might actually be available. Same idea for `distance_km`: `None`
just means the user didn't share a location, not "far away."

See `example_result_handling.py` (new, at the project root) for a small worked
example of safe handling:
```bash
python example_result_handling.py
```
It shows the three-way `is_open_now` → `"open now"` / `"closed right now"` /
`"hours unclear — call ahead to confirm"` mapping, and how `distance_km=None`
should just omit the distance line rather than printing "None km away." Point
Person B at this file directly — it's meant to be copied into the
prompt/explanation layer as-is.

### b) Should `require_open_now` default to `True` for urgency queries?
Right now it defaults to `False` everywhere. Whether the frontend should flip
it to `True` for queries like *"shelter tonight"* is a joint UX call, not
something to decide unilaterally in the retrieval layer — the tradeoff is
precision (only show what's definitely open) vs. recall (a family should
probably still see a great-match shelter even if its hours are unparseable,
rather than have it silently disappear).

To make that conversation concrete, `common.py` now has a `has_urgency_signal(query)`
helper — a cheap keyword check (`"tonight"`, `"emergency"`, `"right now"`, etc.)
that returns `True`/`False`. It's not a replacement for Person B's LLM-based
need extraction, just a fast signal to test the idea against before building
anything fancier:
```python
from common import has_urgency_signal
has_urgency_signal("emergency shelter tonight")  # -> True
```
Suggested default if you don't have time to discuss further: keep
`require_open_now=False`, but have the frontend/explanation layer visibly flag
`is_open_now=False` results ("closed now, but call to confirm") rather than
hiding them — safer than a hard filter that might exclude the best match.

### c) Which backend should Person B build against first?
**Hand off `retrieve_tfidf.py` today.** It works right now with zero setup
cost (no model download, no internet dependency), and its function signature
and return shape are byte-for-byte identical to `retrieve_chroma.py`. Person B
can build their entire prompt/frontend layer against it immediately, then
switch to the Chroma backend later with a one-line import change — no
downstream code changes required. Don't block Person B's start time on
getting the embedding model downloaded and tuned.

---

## 10. Quick troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Make sure `(venv)` shows in your terminal prompt, then `pip install -r requirements.txt` again |
| `command not found: python` | Try `python3` instead of `python` (Mac/Linux default) |
| CSV parsing errors like "Expected N fields, saw N+1" | A field (usually `hours`) has a comma in it and isn't wrapped in quotes — wrap it like `"Tue,Thu 09:00-12:00"` |
| `ingest_chroma.py` hangs or fails to download the model | Needs internet on first run only; check your connection, or ask if the venue Wi-Fi blocks huggingface.co |
| Geocoding returns lots of "no result" | Nominatim needs fairly clean addresses (street, city, state) — try adding zip code |
| Search results all look irrelevant | Check `description` fields aren't empty/generic; run `test_queries.py` to spot-check |

You've got this — the hardest part (getting a working skeleton) is already done and tested. From here it's mostly data quality and iteration.
