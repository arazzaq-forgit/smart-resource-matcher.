"""
example_result_handling.py

NOT part of the retrieval pipeline itself - this is a worked example for
Person B (or anyone building the explanation/prompt layer) showing how to
safely consume the fields that retrieve() can return as None:

  - distance_km:  None if the user didn't share a location
  - is_open_now:  None if the hours string couldn't be confidently parsed
                  (e.g. "Rotating - 1st Sat monthly") - this is NOT the same
                  as closed, and must not be described as closed.

Run it:
    python example_result_handling.py
"""

import sys
sys.path.insert(0, "scripts")

from retrieve_tfidf import TfidfResourceIndex


def describe_hours_status(is_open_now) -> str:
    """Turn the tri-state is_open_now into safe human language.
    Three states, not two - don't collapse None into False."""
    if is_open_now is True:
        return "open now"
    elif is_open_now is False:
        return "closed right now"
    else:  # None
        return "hours unclear — call ahead to confirm"


def describe_distance(distance_km) -> str:
    if distance_km is None:
        return ""  # no location was given, so just omit distance entirely
    return f"{distance_km:.1f} km away"


def build_explanation_prompt_snippet(result: dict, query: str) -> str:
    """Example of the kind of prompt text you'd feed to an LLM for the
    'why this matches' explanation layer. Notice it never asserts
    something the data doesn't actually support."""
    parts = [
        f"Resource: {result['name']} ({result['category']})",
        f"Description: {result['description']}",
        f"Eligibility: {result['eligibility']}",
        f"Status: {describe_hours_status(result['is_open_now'])}",
    ]
    dist = describe_distance(result["distance_km"])
    if dist:
        parts.append(f"Distance: {dist}")
    parts.append(f"\nUser need: {query}")
    parts.append("Write a one-sentence explanation of why this resource matches the user's need.")
    return "\n".join(parts)


if __name__ == "__main__":
    index = TfidfResourceIndex(csv_path="data/resources.csv")

    query = "emergency shelter tonight for my family"
    results = index.retrieve(query, top_k=3)

    for r in results:
        print("-" * 70)
        print(f"{r['name']}")
        print(f"  is_open_now={r['is_open_now']}  ->  \"{describe_hours_status(r['is_open_now'])}\"")
        print(f"  distance_km={r['distance_km']}  ->  \"{describe_distance(r['distance_km']) or '(omitted, no user location)'}\"")

    print("\n--- Example prompt text Person B would send to the LLM ---\n")
    print(build_explanation_prompt_snippet(results[0], query))
