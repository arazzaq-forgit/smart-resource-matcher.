import sys
sys.path.insert(0, "scripts")
from pipeline import get_matches

intent, results = get_matches("my electricity is about to get shut off")
print(intent)
for r in results:
    print(r["score"], r["name"])