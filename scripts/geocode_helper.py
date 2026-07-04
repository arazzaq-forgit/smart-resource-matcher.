"""
geocode_helper.py

If your real dataset has addresses but no lat/lng, use this to fill them in
using Nominatim (OpenStreetMap's free geocoder - no API key needed).

IMPORTANT: Nominatim's usage policy requires max 1 request/second and a
real User-Agent identifying your app. This script respects both.

Usage:
    python scripts/geocode_helper.py data/resources_real.csv
    -> writes data/resources_real_geocoded.csv with lat/lng filled in
"""

import sys
import time
import pandas as pd
from geopy.geocoders import Nominatim

USER_AGENT = "smart-resource-matcher-hackathon-project"  # change to something identifying you


def geocode_csv(input_path: str, output_path: str = None):
    df = pd.read_csv(input_path)
    if "lat" not in df.columns:
        df["lat"] = None
    if "lng" not in df.columns:
        df["lng"] = None

    geolocator = Nominatim(user_agent=USER_AGENT)

    for i, row in df.iterrows():
        if pd.notna(row.get("lat")) and pd.notna(row.get("lng")):
            continue  # already has coordinates

        address = str(row["address"])
        if "phone service" in address.lower() or "withheld" in address.lower():
            continue  # can't geocode a phone-only or confidential service

        try:
            location = geolocator.geocode(address, timeout=10)
        except Exception as e:
            print(f"  [warn] geocoding failed for row {i} ({address}): {e}")
            location = None

        if location:
            df.at[i, "lat"] = location.latitude
            df.at[i, "lng"] = location.longitude
            print(f"  ok: {address} -> ({location.latitude}, {location.longitude})")
        else:
            print(f"  [warn] no result for: {address}")

        time.sleep(1)  # respect Nominatim's 1 req/sec rate limit

    out = output_path or input_path.replace(".csv", "_geocoded.csv")
    df.to_csv(out, index=False)
    print(f"\nSaved -> {out}")
    still_missing = df[df["lat"].isna()]
    if len(still_missing):
        print(f"NOTE: {len(still_missing)} rows still missing coordinates - fill these in manually.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/geocode_helper.py <input_csv> [output_csv]")
        sys.exit(1)
    geocode_csv(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
