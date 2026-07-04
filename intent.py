import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])

VALID_CATEGORIES = [
    "food", "health", "shelter", "legal",
    "financial", "childcare", "mental_health", "other"
]

def extract_intent(query: str) -> dict:
    """Turn a free-text user query into structured filters."""
    prompt = f"""Extract structured information from this request for local help.

Request: "{query}"

Return ONLY a JSON object with these exact fields, no other text:
- "category": one of {VALID_CATEGORIES} that best matches, or null if unclear
- "urgency": "high" if this sounds like an emergency/urgent need (tonight, right now, crisis), otherwise "normal"
- "location_hint": any location mentioned in the request (neighborhood, "downtown", etc.), or null if none
- "cleaned_query": the request rewritten as a short, clear search phrase (remove filler words)
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    return json.loads(raw)


if __name__ == "__main__":
    test_queries = [
        "emergency shelter tonight for my family",
        "mental health counseling sliding scale",
        "free dental care for my kid, no insurance, near downtown",
    ]
    for q in test_queries:
        print("-" * 60)
        print(f"QUERY: {q}")
        print(extract_intent(q))