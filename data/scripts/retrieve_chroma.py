"""
retrieve_chroma.py

The "real" retrieval pipeline: semantic search via sentence-transformers
embeddings stored in Chroma, plus hard filters for category / distance /
open-now. Same return contract as retrieve_tfidf.py, so Person B's code
doesn't need to change when you swap backends.

Prerequisite: run `python scripts/ingest_chroma.py` first to build the index.

Usage:
    python scripts/retrieve_chroma.py
"""

import datetime
from typing import Optional, List, Dict, Any

import chromadb
from sentence_transformers import SentenceTransformer

from common import haversine_km, open_now, VALID_CATEGORIES

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "resources"
MODEL_NAME = "all-MiniLM-L6-v2"


class ChromaResourceIndex:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = client.get_collection(COLLECTION_NAME)

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
        if category is not None and category not in VALID_CATEGORIES:
            raise ValueError(f"Unknown category '{category}'. Valid: {sorted(VALID_CATEGORIES)}")

        query_embedding = self.model.encode([query]).tolist()

        # Pull more than top_k from the vector search so we still have
        # enough candidates left after applying hard filters below.
        raw = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(50, self.collection.count()),
        )

        candidates = []
        for metadata, distance in zip(raw["metadatas"][0], raw["distances"][0]):
            if category is not None and metadata.get("category") != category:
                continue

            # Chroma's default distance is smaller = more similar; convert
            # to a 0-1-ish "higher is better" score for consistency with the
            # TF-IDF backend.
            score = 1 / (1 + float(distance))

            distance_km = None
            if user_lat is not None and user_lng is not None:
                try:
                    distance_km = haversine_km(user_lat, user_lng, float(metadata["lat"]), float(metadata["lng"]))
                except (TypeError, ValueError, KeyError):
                    distance_km = None
                if max_distance_km is not None and distance_km is not None and distance_km > max_distance_km:
                    continue

            is_open = open_now(metadata.get("hours", ""), current_dt)
            if require_open_now and is_open is False:
                continue

            adjusted_score = score
            if distance_km is not None:
                adjusted_score += max(0, (10 - distance_km)) * 0.002

            candidates.append({
                "id": int(metadata.get("id", 0)),
                "name": metadata.get("name", "Unknown"),
                "category": metadata.get("category", "other"),
                "description": metadata.get("description", ""),
                "eligibility": metadata.get("eligibility", ""),
                "address": metadata.get("address", ""),
                "hours": metadata.get("hours", ""),
                "phone": metadata.get("phone", ""),
                "website": metadata.get("website", ""),
                "walk_in": metadata.get("walk_in", "False") == "True",
                "last_verified": metadata.get("last_verified", ""),
                "score": round(adjusted_score, 4),
                "distance_km": round(distance_km, 2) if distance_km is not None else None,
                "is_open_now": is_open,
            })

        candidates.sort(key=lambda c: c["score"], reverse=True)
        return candidates[:top_k]


if __name__ == "__main__":
    index = ChromaResourceIndex()
    for q in [
        "I need free dental care for my kid, no insurance, near downtown",
        "emergency shelter tonight for my family",
    ]:
        print(f"\nQUERY: {q}")
        for r in index.retrieve(q, top_k=3):
            print(f"  [{r['score']}] {r['name']} ({r['category']})")