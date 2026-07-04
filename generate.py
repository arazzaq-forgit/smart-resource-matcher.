import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])

def describe_hours_status(is_open_now) -> str:
    if is_open_now is True:
        return "open now"
    elif is_open_now is False:
        return "closed right now"
    else:
        return "hours unclear — call ahead to confirm"

def describe_distance(distance_km) -> str:
    if distance_km is None:
        return None
    return f"{distance_km:.1f} km away"

def generate_response(query: str, results: list[dict]) -> dict:
    if not results:
        return {"results": [], "note": "No matching resources found for this request."}

    resource_block = ""
    for i, r in enumerate(results):
        dist = describe_distance(r["distance_km"])
        resource_block += f"""
Resource {i+1}:
- name: {r['name']}
- category: {r['category']}
- description: {r['description']}
- eligibility: {r['eligibility']}
- status: {describe_hours_status(r['is_open_now'])}
- distance: {dist if dist else 'unknown'}
"""

    prompt = f"""A person asked for help with this need: "{query}"

Here are {len(results)} candidate resources, ranked by relevance:
{resource_block}

For each resource, write ONE short sentence explaining why it matches the person's need,
using ONLY the facts given above — do not invent details, hours, or eligibility not listed.
If a resource's status is "hours unclear", mention that instead of guessing.

Return ONLY a JSON object in this exact shape, no other text:
{{
  "results": [
    {{"name": "...", "why": "...", "status": "..."}}
  ],
  "note": "one sentence overall note, or empty string if nothing notable"
}}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "scripts")
    from pipeline import get_matches

    query = "emergency shelter tonight for my family"
    intent, results = get_matches(query)
    output = generate_response(query, results)

    print(json.dumps(output, indent=2))