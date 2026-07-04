"""
test_queries.py

Step 7 from the guide: run a batch of realistic queries and sanity-check
that the top results actually make sense. Run this from the project root:

    python test_queries.py

If results look bad for a query, it's almost always one of:
  1. The resource's `description` field is too thin -> add more detail.
  2. top_k is too small/large -> tune it.
  3. (TF-IDF only) the query and description just don't share enough words
     -> this is exactly the problem sentence-transformers embeddings fix,
     since they match on MEANING not exact words.
"""

import sys
sys.path.insert(0, "scripts")

from retrieve_tfidf import TfidfResourceIndex

QUERIES = [
    "I need free dental care for my kid, no insurance, near downtown",
    "emergency shelter tonight for my family",
    "mental health counseling sliding scale",
    "help I'm about to lose my apartment eviction",
    "free food this week no questions asked",
    "diapers for my baby I can't afford",
    "domestic violence need somewhere safe",
    "my electricity is about to get shut off",
    "job help I just got laid off",
    "childcare for my toddler while I work",
    "free eye exam glasses",
    "someone to talk to right now I'm in crisis",
    "immigration legal help",
    "senior meal delivery",
    "veteran housing assistance",
]

if __name__ == "__main__":
    index = TfidfResourceIndex(csv_path="data/resources_sample.csv")

    for q in QUERIES:
        print("=" * 90)
        print(f"QUERY: {q}")
        results = index.retrieve(q, top_k=3)
        if not results:
            print("  ⚠️  NO RESULTS - investigate")
            continue
        for r in results:
            flag = "⚠️ " if r["score"] < 0.05 else "   "
            print(f"{flag}[{r['score']}] {r['name']}  ({r['category']})")
    print("=" * 90)
    print("\nDone. Scroll up for any ⚠️ low-confidence matches worth investigating.")
