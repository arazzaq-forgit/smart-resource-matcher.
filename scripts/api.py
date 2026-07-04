"""
api.py

Tiny FastAPI wrapper exposing retrieve() as an HTTP endpoint, in case
Person B wants to call your pipeline over HTTP instead of importing it
directly as a Python function.

Run:
    uvicorn scripts.api:app --reload --port 8000

Then test:
    http://127.0.0.1:8000/retrieve?query=free dental care for my kid&top_k=3

Swap USE_CHROMA to True once you've run ingest_chroma.py and want the
real embedding-based backend instead of TF-IDF.
"""

from fastapi import FastAPI, Query
from typing import Optional

USE_CHROMA = False  # flip to True after running scripts/ingest_chroma.py

if USE_CHROMA:
    from retrieve_chroma import ChromaResourceIndex as ResourceIndex
else:
    from retrieve_tfidf import TfidfResourceIndex as ResourceIndex

app = FastAPI(title="Smart Resource Matcher - Retrieval API")
index = ResourceIndex()


@app.get("/retrieve")
def retrieve(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None,
    user_lat: Optional[float] = None,
    user_lng: Optional[float] = None,
    max_distance_km: Optional[float] = None,
    require_open_now: bool = False,
):
    results = index.retrieve(
        query=query,
        top_k=top_k,
        category=category,
        user_lat=user_lat,
        user_lng=user_lng,
        max_distance_km=max_distance_km,
        require_open_now=require_open_now,
    )
    return {"query": query, "results": results}


@app.get("/health")
def health():
    return {"status": "ok"}
