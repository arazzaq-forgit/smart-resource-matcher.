import sys
sys.path.insert(0, "scripts")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from pipeline import get_matches
from generate import generate_response
from followup import answer_followup

app = FastAPI()

# Allow the deployed frontend (and local dev) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for hackathon speed; tighten to your Vercel URL before final submission if time allows
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    user_lat: Optional[float] = None
    user_lng: Optional[float] = None

class FollowupRequest(BaseModel):
    question: str
    previous_results: List[dict]
    conversation_history: Optional[List[dict]] = None

@app.post("/query")
def query(payload: QueryRequest):
    intent, results = get_matches(
        payload.query,
        top_k=payload.top_k,
        user_lat=payload.user_lat,
        user_lng=payload.user_lng,
    )
    explanation = generate_response(payload.query, results)

    # Merge the LLM explanation ("why", "status") back into the FULL resource
    # objects, instead of dropping name/address/phone/hours/distance/score.
    explained_by_name = {r["name"]: r for r in explanation.get("results", [])}
    merged_results = []
    for r in results:
        extra = explained_by_name.get(r["name"], {})
        merged_results.append({
            **r,  # full original fields: name, category, description, eligibility,
                  # address, phone, website, hours, walk_in, distance_km,
                  # is_open_now, score, last_verified
            "why": extra.get("why", ""),
        })

    return {
        "intent": intent,
        "results": merged_results,
        "note": explanation.get("note", ""),
    }

@app.post("/followup")
def followup(payload: FollowupRequest):
    return answer_followup(
        payload.question,
        payload.previous_results,
        payload.conversation_history,
    )
