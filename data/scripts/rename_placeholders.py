"""
rename_placeholders.py

Takes the combined dataset and replaces the "[SAMPLE] <generic type>" names
with varied, realistic-sounding organization names - one per row, no repeats.

IMPORTANT: this only changes the display `name`. The `description` field
still contains the "PLACEHOLDER ENTRY... not a verified real organization"
disclosure. That's intentional and kept on purpose: these rows have
invented addresses and phone numbers, and a tool like this could plausibly
be used by someone in a real crisis (e.g. "emergency shelter tonight"). A
fake name with zero indication anywhere that it's fake is the difference
between "obviously a placeholder" and "someone calls a number that doesn't
exist during an actual emergency." Renaming the surface label is fine;
removing all disclosure is not.

Usage:
    python scripts/rename_placeholders.py <input_csv> <output_csv>
"""

import random
import sys
import pandas as pd

random.seed(7)

# Name-building blocks, varied per category so results feel distinct rather
# than templated. None of these are real organization names.
PREFIXES = [
    "Harbor", "Cornerstone", "Beacon", "Unity", "Bridgepoint", "Willow",
    "Hearth", "Anchor", "Horizon", "Guiding Star", "Mosaic", "Serenity",
    "Alcove", "Foothill", "Riverside", "Gateway", "Kindred", "Lighthouse",
    "Open Door", "New Leaf", "Compass", "Evergreen", "Threshold", "Haven",
]

SUFFIX_BY_CATEGORY = {
    "food": ["Community Pantry", "Food Collective", "Nourish Network", "Grocery Assistance Program", "Meal Share Center"],
    "shelter": ["Emergency Shelter", "Family Housing Center", "Refuge House", "Overnight Shelter Program", "Housing Crisis Center"],
    "legal": ["Legal Aid Center", "Justice Clinic", "Legal Advocacy Group", "Rights & Advocacy Center", "Legal Services Collective"],
    "financial": ["Financial Assistance Center", "Economic Support Program", "Relief Fund", "Financial Wellness Center", "Assistance Network"],
    "childcare": ["Family Resource Center", "Early Learning Program", "Childcare Assistance Network", "Parent & Child Center", "Family Support Program"],
    "mental_health": ["Counseling Center", "Wellness Collective", "Behavioral Health Clinic", "Mental Health Support Center", "Therapy Access Program"],
    "other": ["Community Resource Center", "Support Network", "Outreach Center", "Resource Hub", "Community Services Center"],
}


def generate_names(category: str, count: int):
    """Generate `count` unique-within-category names for a category."""
    suffixes = SUFFIX_BY_CATEGORY.get(category, ["Community Resource Center"])
    combos = [(p, s) for p in PREFIXES for s in suffixes]
    random.shuffle(combos)
    if count > len(combos):
        raise ValueError(f"Not enough unique name combinations for category={category}")
    return [f"{p} {s}" for p, s in combos[:count]]


def rename_placeholders(input_path: str, output_path: str):
    df = pd.read_csv(input_path)
    mask = df["name"].astype(str).str.startswith("[SAMPLE]")

    new_names = []
    for category in df.loc[mask, "category"].unique():
        cat_mask = mask & (df["category"] == category)
        count = cat_mask.sum()
        names = generate_names(category, count)
        df.loc[cat_mask, "name"] = names

    df.to_csv(output_path, index=False)
    print(f"Renamed {mask.sum()} placeholder rows -> {output_path}")
    print("\nSample renamed rows:")
    print(df.loc[mask, ["id", "name", "category"]].head(10).to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/rename_placeholders.py <input_csv> <output_csv>")
        sys.exit(1)
    rename_placeholders(sys.argv[1], sys.argv[2])
