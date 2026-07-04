"""
retrieve_tfidf.py

QUICK-START retrieval pipeline. Uses TF-IDF + cosine similarity instead of
a neural embedding model, so it needs zero internet access and zero API
keys. Great for getting something working in the first hour, or as your
demo's fallback if Wi-Fi at the venue is bad.

Swap this out for retrieve_chroma.py (sentence-transformers + Chroma) once
you have time - same function signature, so Person B's code doesn't change.

Usage:
    python scripts/retrieve_tfidf.py
"""

import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from common import load_resources, haversine_km, open_now, VALID_CATEGORIES

DEFAULT_CSV_PATH = "data/resources_sample.csv"


class TfidfResourceIndex:
    def __init__(self, csv_path: str = DEFAULT_CSV_PATH):
        self.df = load_resources(csv_path)
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.doc_matrix = self.vectorizer.fit_transform(self.df["embed_text"])

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
        max_distance_km: Optional[float] = None,
        require_open_now: bool = False,
        current_dt: Optional[datetime.datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        This is the CONTRACT Person B's code depends on. Keep the return
        shape stable even if you swap the backend.

        Returns a list of dicts, each:
            {
              "id", "name", "category", "description", "eligibility",
              "address", "hours", "phone", "website", "walk_in",
              "last_verified",
              "score": float,             # similarity score, higher = better
              "distance_km": float|None,  # None if no user location given
              "is_open_now": bool|None,   # None if hours unparseable
            }
        Sorted best-match first.
        """
        if category is not None and category not in VALID_CATEGORIES:
            raise ValueError(f"Unknown category '{category}'. Valid: {sorted(VALID_CATEGORIES)}")

        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.doc_matrix)[0]

        candidates = []
        for idx, row in self.df.iterrows():
            score = float(sims[idx])

            if category is not None and row["category"] != category:
                continue

            distance_km = None
            if user_lat is not None and user_lng is not None:
                try:
                    distance_km = haversine_km(user_lat, user_lng, float(row["lat"]), float(row["lng"]))
                except (TypeError, ValueError):
                    distance_km = None
                if max_distance_km is not None and distance_km is not None and distance_km > max_distance_km:
                    continue

            is_open = open_now(row["hours"], current_dt)
            if require_open_now and is_open is False:
                continue
            # Note: is_open is None (unknown/rotating hours) is NOT excluded -
            # better to surface it with a caveat than hide a possibly-useful resource.

            # Simple re-rank: semantic score is primary, distance is a mild
            # tiebreaker boost. Tune these weights based on Step 7 testing.
            adjusted_score = score
            if distance_km is not None:
                adjusted_score += max(0, (10 - distance_km)) * 0.002

            candidates.append({
                "id": int(row["id"]),
                "name": row["name"],
                "category": row["category"],
                "description": row["description"],
                "eligibility": row["eligibility"],
                "address": row["address"],
                "hours": row["hours"],
                "phone": row["phone"],
                "website": row["website"],
                "walk_in": bool(row["walk_in"]),
                "last_verified": row["last_verified"],
                "score": round(adjusted_score, 4),
                "distance_km": round(distance_km, 2) if distance_km is not None else None,
                "is_open_now": is_open,
            })

        candidates.sort(key=lambda c: c["score"], reverse=True)
        return candidates[:top_k]


if __name__ == "__main__":
    index = TfidfResourceIndex()

    test_queries = [
        "I need free dental care for my kid, no insurance, near downtown",
        "emergency shelter tonight for my family",
        "mental health counseling sliding scale",
        "help I'm about to lose my apartment eviction",
        "free food this week no questions asked",
        "diapers for my baby I can't afford",
    ]

    for q in test_queries:
        print("=" * 80)
        print(f"QUERY: {q}")
        results = index.retrieve(q, top_k=3)
        for r in results:
            print(f"  [{r['score']}] {r['name']} ({r['category']}) - open_now={r['is_open_now']}")
            print(f"       eligibility: {r['eligibility']}")
        print()
