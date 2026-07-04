"""
common.py
Shared helper functions used by both the TF-IDF quick-start pipeline
and the "real" sentence-transformers + Chroma pipeline.

Nothing in this file requires internet access - safe to run anywhere.
"""

import math
import re
import datetime
import pandas as pd

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_INDEX = {d: i for i, d in enumerate(DAY_NAMES)}


# ---------------------------------------------------------------------------
# 1. Loading data
# ---------------------------------------------------------------------------
def load_resources(csv_path: str) -> pd.DataFrame:
    """Load the resources CSV and build the 'embed_text' field that gets
    turned into vectors. If you add new columns, decide whether they should
    be folded into embed_text (helps semantic matching) or kept as pure
    metadata (used for hard filters only)."""
    df = pd.read_csv(csv_path)

    required = [
        "id", "name", "category", "description", "eligibility",
        "address", "lat", "lng", "hours", "phone", "website",
        "walk_in", "last_verified",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"resources CSV is missing required columns: {missing}")

    if df["description"].isna().any() or (df["description"].astype(str).str.strip() == "").any():
        bad_ids = df[df["description"].isna() | (df["description"].astype(str).str.strip() == "")]["id"].tolist()
        raise ValueError(f"These resource ids have empty descriptions (will break embeddings): {bad_ids}")

    df["category"] = df["category"].str.strip().str.lower()

    # This is the text that actually gets embedded. Tune this if search
    # quality is poor - usually the fix is "add more detail here", not a
    # fancier model.
    df["embed_text"] = (
        df["name"].astype(str) + ". "
        + df["category"].astype(str) + ". "
        + df["description"].astype(str) + " "
        + "Eligibility: " + df["eligibility"].astype(str)
    )

    return df


# ---------------------------------------------------------------------------
# 2. Distance
# ---------------------------------------------------------------------------
def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """Great-circle distance in kilometers between two lat/lng points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# 3. Hours parsing / "open now" logic
# ---------------------------------------------------------------------------
# Supported formats in the sample data (extend as needed for real data):
#   "24/7"
#   "Mon-Fri 08:00-17:00"
#   "Tue,Thu 09:00-12:00"        (comma list, no dash)
#   "Mon,Wed,Fri 08:30-15:30"
#   "Rotating - 1st Sat monthly 09:00-14:00"   -> treated as unknown/skip
#   "Nov-Mar daily 18:00-08:00"                -> treated as unknown/skip
#
# For a hackathon, "unknown" hours should NOT be filtered out when the user
# asks for "open now" - better to show it with a caveat than hide a resource
# that might actually help. That's why open_now() returns True/False/None.

_TIME_RANGE_RE = re.compile(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})")
_DAY_RANGE_RE = re.compile(r"^([A-Za-z]{3})-([A-Za-z]{3})$")


def _parse_day_token(token: str):
    """'Mon-Fri' -> [0,1,2,3,4]; 'Tue,Thu' -> [1,3]; 'Mon' -> [0]"""
    token = token.strip()
    days = set()
    for part in token.split(","):
        part = part.strip()
        m = _DAY_RANGE_RE.match(part)
        if m:
            start, end = m.group(1), m.group(2)
            if start in DAY_INDEX and end in DAY_INDEX:
                s, e = DAY_INDEX[start], DAY_INDEX[end]
                if s <= e:
                    days.update(range(s, e + 1))
                else:  # wraps around the week
                    days.update(list(range(s, 7)) + list(range(0, e + 1)))
        elif part in DAY_INDEX:
            days.add(DAY_INDEX[part])
    return days


def open_now(hours_str: str, current_dt: datetime.datetime = None):
    """Returns True/False if we can determine open status, or None if the
    hours string is in a format we don't confidently parse (e.g. rotating
    schedules) - callers should treat None as 'unknown, don't exclude'."""
    if current_dt is None:
        current_dt = datetime.datetime.now()

    if not isinstance(hours_str, str) or not hours_str.strip():
        return None

    h = hours_str.strip()

    if h.upper() == "24/7":
        return True

    if "rotating" in h.lower() or "monthly" in h.lower():
        return None  # too irregular to parse confidently

    time_match = _TIME_RANGE_RE.search(h)
    if not time_match:
        return None

    open_t, close_t = time_match.groups()
    try:
        open_h, open_m = map(int, open_t.split(":"))
        close_h, close_m = map(int, close_t.split(":"))
    except ValueError:
        return None

    day_part = h[: time_match.start()].strip()

    if day_part.lower() == "daily":
        day_set = set(range(7))
    else:
        day_set = _parse_day_token(day_part)
        if not day_set:
            return None  # couldn't parse days confidently

    weekday = current_dt.weekday()  # Mon=0 ... Sun=6
    if weekday not in day_set:
        return False

    now_minutes = current_dt.hour * 60 + current_dt.minute
    open_minutes = open_h * 60 + open_m
    close_minutes = close_h * 60 + close_m

    if close_minutes <= open_minutes:
        # overnight window, e.g. 18:00-08:00
        return now_minutes >= open_minutes or now_minutes <= close_minutes
    return open_minutes <= now_minutes <= close_minutes


VALID_CATEGORIES = {
    "food", "health", "shelter", "legal", "financial",
    "childcare", "mental_health", "other",
}


# ---------------------------------------------------------------------------
# 4. Urgency detection (helper for the require_open_now decision)
# ---------------------------------------------------------------------------
# Cheap keyword heuristic - NOT a replacement for Person B's LLM-based need
# extraction, just a fast signal you two can use while deciding defaults.
# Returns True if the query sounds time-sensitive ("tonight", "right now",
# "emergency", etc.), else False. Never returns None - this is a boolean
# signal, unrelated to the is_open_now field's True/False/None on results.
_URGENCY_WORDS = {
    "tonight", "now", "right now", "immediately", "emergency", "urgent",
    "asap", "today", "crisis", "help now",
}


def has_urgency_signal(query: str) -> bool:
    q = query.lower()
    return any(word in q for word in _URGENCY_WORDS)
