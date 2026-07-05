"""
ingest_chroma.py

The "real" pipeline: embeds every resource with a sentence-transformers
model and stores the vectors + metadata in a local Chroma database.

Run this ONCE (or whenever resources.csv changes) to build/rebuild the index:
    python scripts/ingest_chroma.py

Requires internet on first run (to download the embedding model, ~80MB).
After that it runs fully offline.
"""

import chromadb
from sentence_transformers import SentenceTransformer

from common import load_resources

CSV_PATH = "data/resources.csv"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "resources"
MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, good enough for a hackathon


def build_index(csv_path: str = CSV_PATH):
    print(f"Loading resources from {csv_path} ...")
    df = load_resources(csv_path)

    print(f"Loading embedding model '{MODEL_NAME}' (downloads on first run) ...")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Embedding {len(df)} resources ...")
    embeddings = model.encode(df["embed_text"].tolist(), show_progress_bar=True).tolist()

    print(f"Writing to Chroma at ./{CHROMA_DIR} ...")
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Start fresh each time so re-running this script after editing the CSV
    # doesn't leave stale/duplicate entries around.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    collection.add(
        ids=[str(i) for i in df["id"].tolist()],
        embeddings=embeddings,
        documents=df["embed_text"].tolist(),
        metadatas=df.drop(columns=["embed_text"]).astype(str).to_dict(orient="records"),
    )

    print(f"Done. Indexed {collection.count()} resources into collection '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    build_index()
