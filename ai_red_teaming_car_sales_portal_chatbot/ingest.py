
from pathlib import Path
import uuid
import httpx
import chromadb

OLLAMA_BASE = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
DATA_DIR = Path("data")
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "car_sales_docs"


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 120) -> list[str]:
    text = text.strip()
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    with httpx.Client(timeout=120) as client:
        resp = client.post(
            f"{OLLAMA_BASE}/api/embed",
            json={"model": EMBED_MODEL, "input": texts},
        )
        resp.raise_for_status()
        return resp.json()["embeddings"]


def main():
    chroma = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma.get_or_create_collection(name=COLLECTION_NAME)

    docs = []
    metadatas = []
    ids = []

    for path in DATA_DIR.glob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, chunk in enumerate(chunk_text(text)):
            docs.append(chunk)
            metadatas.append({"source": path.name, "chunk": i})
            ids.append(str(uuid.uuid4()))

    if not docs:
        print("No text documents found in ./data")
        return

    embeddings = embed_texts(docs)
    collection.add(ids=ids, documents=docs, metadatas=metadatas, embeddings=embeddings)
    print(f"Ingested {len(docs)} chunks into '{COLLECTION_NAME}'")


if __name__ == "__main__":
    main()
