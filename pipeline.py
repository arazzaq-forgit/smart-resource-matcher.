import sys
import os
from dotenv import load_dotenv
sys.path.insert(0, "scripts")

from retrieve_tfidf import TfidfResourceIndex
from intent import extract_intent

load_dotenv()
CSV_PATH = os.environ.get("RESOURCE_CSV_PATH", "data/resources_sample.csv")
index = TfidfResourceIndex(csv_path=CSV_PATH)

def get_matches(query: str, top_k: int = 5, user_lat=None, user_lng=None):
    intent = extract_intent(query)

    results = index.retrieve(
        query=intent["cleaned_query"],
        top_k=top_k,
        category=intent["category"],
        user_lat=user_lat,
        user_lng=user_lng,
        require_open_now=(intent["urgency"] == "high"),
    )

    return intent, results


if __name__ == "__main__":
    query = "emergency shelter tonight for my family"
    intent, results = get_matches(query)

    print("INTENT:", intent)
    print()
    for r in results:
        print(f"[{r['score']:.4f}] {r['name']}  ({r['category']})  open_now={r['is_open_now']}")
