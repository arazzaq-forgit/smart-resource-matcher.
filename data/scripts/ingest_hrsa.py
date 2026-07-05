"""
ingest_hrsa.py

Turns the HRSA Health Center Service Delivery Sites national CSV into rows
matching data/resources_sample.csv's schema, filtered to your state/city.

SOURCE: HRSA Health Center Service Delivery and Look-Alike Sites (public
federal data, Bureau of Primary Health Care - "Usage limitations: None").
  https://data.hrsa.gov/data/download

VERIFIED against a real downloaded copy (18,938 rows, 56 columns) - the
column names below are confirmed, not guessed.

STEP 1 - put your downloaded CSV here:
    data/raw_hrsa_sites.csv

STEP 2 (optional, only if a future HRSA release renames columns) - run:
    python scripts/ingest_hrsa.py --inspect
to print the real headers and confirm nothing changed.

STEP 3 - filter to your city/state and convert to our schema:
    python scripts/ingest_hrsa.py --state TX --city Austin

This writes data/resources_hrsa_filtered.csv, ready to concatenate with
your manually-curated shelter/legal/financial/childcare rows.
"""

import argparse
import sys
import pandas as pd

RAW_CSV_PATH = "data/raw_hrsa_sites.csv"
OUTPUT_PATH = "data/resources_hrsa_filtered.csv"

# ---------------------------------------------------------------------------
# Confirmed against a real HRSA download (56 columns). If a future release
# renames something, run --inspect and fix this.
# ---------------------------------------------------------------------------
COLUMN_MAP = {
    "name": "Site Name",
    "address": "Site Address",
    "city": "Site City",
    "state": "Site State Abbreviation",
    "zip": "Site Postal Code",
    "phone": "Site Telephone Number",
    "website": "Site Web Address",
    "lat": "Geocoding Artifact Address Primary Y Coordinate",   # Y = latitude
    "lng": "Geocoding Artifact Address Primary X Coordinate",   # X = longitude
    "hc_type": "Health Center Type",                             # FQHC vs FQHC Look-Alike
    "site_role": "Health Center Type Description",               # Service Delivery Site vs Administrative
    "location_setting": "Health Center Service Delivery Site Location Setting Description",  # School, Hospital, etc.
    "schedule": "Health Center Operational Schedule Description",  # Full-Time / Part-Time / Unknown - NOT clock hours
    "status": "Site Status Description",                          # should be "Active"
}

# Rows where site_role is one of these are administrative-only addresses,
# not places a patient can actually go - excluded by default.
EXCLUDE_SITE_ROLES = {"Administrative"}


def inspect(raw_path: str):
    df = pd.read_csv(raw_path, nrows=5, low_memory=False)
    print(f"\n{len(df.columns)} columns found:\n")
    for c in df.columns:
        print(f"  - {c}")
    print("\nFirst 2 sample rows:\n")
    print(df.head(2).to_string())
    print(
        "\nNow open the metadata xlsx, confirm these match what you expect, "
        "then edit COLUMN_MAP at the top of this script if any names differ."
    )


def build_description(row) -> str:
    """HRSA's data has no free-text description field, so we template one,
    folding in real detail from the row (site type, location setting) so
    it's not generic boilerplate - this is what gets embedded and searched."""
    hc_type = str(row.get(COLUMN_MAP["hc_type"], "")).strip()
    setting = str(row.get(COLUMN_MAP["location_setting"], "")).strip()

    base = (
        "Federally supported community health center offering primary care "
        "services. Serves patients regardless of insurance status or ability "
        "to pay, with services often available on a sliding fee scale."
    )
    if setting and setting.lower() not in ("nan", "unknown", "all other clinic types"):
        base += f" This location operates as a {setting.lower()}-based site."
    if hc_type and hc_type.lower() != "nan":
        base += f" Designated as a {hc_type}."
    return base


def run(state: str, city: str, raw_path: str, output_path: str, max_rows: int = None):
    df = pd.read_csv(raw_path, low_memory=False)

    missing = [v for v in COLUMN_MAP.values() if v not in df.columns]
    if missing:
        print(f"ERROR: these expected columns were not found in your CSV: {missing}")
        print("Run with --inspect to see the real column names and fix COLUMN_MAP.")
        sys.exit(1)

    if state:
        df = df[df[COLUMN_MAP["state"]].astype(str).str.upper() == state.upper()]
    if city:
        df = df[df[COLUMN_MAP["city"]].astype(str).str.upper() == city.upper()]

    before = len(df)
    df = df[~df[COLUMN_MAP["site_role"]].isin(EXCLUDE_SITE_ROLES)]
    excluded = before - len(df)

    print(f"{before} rows match state={state!r} city={city!r} ({excluded} excluded as administrative-only)")
    if len(df) == 0:
        print("No matches - check spelling/abbreviation (state should be 2-letter, e.g. 'TX').")
        sys.exit(1)

    if max_rows:
        df = df.head(max_rows)

    out_rows = []
    next_id = 1000  # offset so these ids don't collide with your manually curated rows
    for _, row in df.iterrows():
        full_address = ", ".join(
            str(row.get(COLUMN_MAP[k], "")).strip()
            for k in ["address", "city", "state", "zip"]
            if str(row.get(COLUMN_MAP[k], "")).strip() not in ("", "nan")
        )
        website = str(row.get(COLUMN_MAP["website"], "")).strip()
        website = "" if website.lower() == "nan" else website

        out_rows.append({
            "id": next_id,
            "name": row.get(COLUMN_MAP["name"], ""),
            "category": "health",
            "description": build_description(row),
            "eligibility": "Uninsured and underinsured accepted; sliding fee scale based on income",
            "address": full_address,
            "lat": row.get(COLUMN_MAP["lat"], ""),
            "lng": row.get(COLUMN_MAP["lng"], ""),
            "hours": "Call to confirm hours",  # HRSA file doesn't include structured hours - see note below
            "phone": row.get(COLUMN_MAP["phone"], ""),
            "website": website,
            "walk_in": "",  # unknown from this dataset - leave blank rather than guess
            "last_verified": pd.Timestamp.today().strftime("%Y-%m-%d"),
        })
        next_id += 1

    out_df = pd.DataFrame(out_rows)
    out_df.to_csv(output_path, index=False)
    print(f"Wrote {len(out_df)} rows -> {output_path}")
    print(
        "\nNOTE: 'hours' is a placeholder ('Call to confirm hours') because this "
        "HRSA file doesn't include structured open/close times. That's fine - "
        "our open_now() parser already returns None (not False) for unparseable "
        "hours, so these sites won't be wrongly marked closed. If you have time, "
        "backfill real hours for your highest-traffic sites."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true", help="Print columns and sample rows, then exit")
    parser.add_argument("--state", type=str, default=None, help="2-letter state code, e.g. TX")
    parser.add_argument("--city", type=str, default=None, help="City name, must match HRSA's spelling")
    parser.add_argument("--raw", type=str, default=RAW_CSV_PATH)
    parser.add_argument("--out", type=str, default=OUTPUT_PATH)
    parser.add_argument("--max-rows", type=int, default=None, help="Cap the number of output rows")
    args = parser.parse_args()

    if args.inspect:
        inspect(args.raw)
    else:
        if not args.state and not args.city:
            print("Pass at least --state (recommended) to keep the ~16,000 rows manageable.")
            sys.exit(1)
        run(args.state, args.city, args.raw, args.out, args.max_rows)
