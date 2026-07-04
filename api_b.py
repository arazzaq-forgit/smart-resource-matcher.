import sys
sys.path.insert(0, "scripts")

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from pipeline import get_matches
from generate import generate_response

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None

@app.post("/query")
def query(payload: QueryRequest):
    intent, results = get_matches(
        payload.query,
        top_k=payload.top_k,
        user_lat=payload.user_lat,
        user_lng=payload.user_lng,
    )
    response = generate_response(payload.query, results)
    return {
        "intent": intent,
        "response": response,
    }