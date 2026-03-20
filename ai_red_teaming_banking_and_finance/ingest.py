"""
Ingest documents into ChromaDB for RAG.

This script reads text files from the docs/ directory and creates
embeddings using the Ollama API, then stores them in ChromaDB.

Usage:
    python ingest.py
"""

import chromadb
from openai import OpenAI
from pathlib import Path


# Configuration
OPENAI_BASE_URL = "http://localhost:11434/v1"
OPENAI_API_KEY = "ollama"
EMBED_MODEL = "nomic-embed-text"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "banking_docs"
DOCS_DIR = Path("docs")
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


def main():
    print("🏦 Banking & Finance RAG Ingestion")
    print("=" * 50)

    # Initialize OpenAI client for embeddings
    client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)

    # Initialize ChromaDB
    chroma = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete existing collection if it exists
    try:
        chroma.delete_collection(name=COLLECTION_NAME)
        print(f"🗑️  Deleted existing collection: {COLLECTION_NAME}")
    except Exception:
        pass

    collection = chroma.create_collection(name=COLLECTION_NAME)
    print(f"📁 Created collection: {COLLECTION_NAME}")

    # Process documents
    if not DOCS_DIR.exists():
        print(f"⚠️  Docs directory not found: {DOCS_DIR}")
        return

    doc_files = list(DOCS_DIR.glob("*.txt"))
    if not doc_files:
        print(f"⚠️  No .txt files found in {DOCS_DIR}")
        return

    total_chunks = 0

    for doc_path in doc_files:
        print(f"\n📄 Processing: {doc_path.name}")

        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = chunk_text(content)
        print(f"   Split into {len(chunks)} chunks")

        # Generate embeddings
        print(f"   Generating embeddings...")
        embeddings_response = client.embeddings.create(
            model=EMBED_MODEL,
            input=chunks
        )

        embeddings = [item.embedding for item in embeddings_response.data]

        # Add to ChromaDB
        ids = [f"{doc_path.stem}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": doc_path.name, "chunk": i} for i in range(len(chunks))]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

        total_chunks += len(chunks)
        print(f"   ✅ Added {len(chunks)} chunks to collection")

    print(f"\n{'=' * 50}")
    print(f"✅ Ingestion complete!")
    print(f"   Total documents: {len(doc_files)}")
    print(f"   Total chunks: {total_chunks}")
    print(f"   Collection: {COLLECTION_NAME}")
    print(f"   Storage: {CHROMA_DIR}")


if __name__ == "__main__":
    main()
