#!/usr/bin/env python
"""
Script: ingest_knowledge.py

Reads Markdown knowledge files listed in domain_config.json
and ingests them as vector embeddings into Qdrant.

Usage (from project root):
    python knowledge/processed/farmacia_demo/scripts/ingest_knowledge.py
"""
import argparse
import json
import os
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from openai import OpenAI

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "domain_config.json"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def chunk_markdown(text: str, source: str, chunk_size: int = 400) -> list[dict]:
    """Paragraph-based chunking. Works for any Markdown file."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[dict] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) > chunk_size and current:
            chunks.append({"text": current.strip(), "source": source})
            current = para
        else:
            current = (current + "\n\n" + para).strip()

    if current:
        chunks.append({"text": current.strip(), "source": source})

    return chunks


def get_embedding(client: OpenAI, text: str) -> list[float]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def ensure_collection(qdrant: QdrantClient, collection_name: str) -> None:
    existing = [c.name for c in qdrant.get_collections().collections]
    if collection_name not in existing:
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        print(f"✅ Collection '{collection_name}' created.")
    else:
        print(f"ℹ️  Collection '{collection_name}' already exists.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest knowledge Markdown files into Qdrant")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to domain_config.json")
    args = parser.parse_args()

    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY is not set. Exiting.")
        sys.exit(1)

    config = load_config(args.config)
    knowledge_cfg = config.get("knowledge", {})
    domain_id = config.get("domain_id", "unknown")
    collection_name: str = knowledge_cfg.get("qdrant_collection", "knowledge_base")
    chunk_size: int = knowledge_cfg.get("chunk_size", 400)
    file_paths: list[str] = knowledge_cfg.get("files", [])

    print(f"Domain: {domain_id} | Collection: {collection_name}")
    qdrant = QdrantClient(url=QDRANT_URL)
    ensure_collection(qdrant, collection_name)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    all_chunks: list[dict] = []
    for file_str in file_paths:
        path = PROJECT_ROOT / file_str
        if not path.exists():
            print(f"⚠️  File not found, skipping: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        chunks = chunk_markdown(text, source=path.name, chunk_size=chunk_size)
        all_chunks.extend(chunks)
        print(f"  → {path.name}: {len(chunks)} chunks")

    if not all_chunks:
        print("⚠️  No chunks to ingest. Check your knowledge.files config.")
        return

    print(f"\nEmbedding and uploading {len(all_chunks)} chunks...")
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=get_embedding(openai_client, chunk["text"]),
            payload={"text": chunk["text"], "source": chunk["source"], "domain_id": domain_id},
        )
        for chunk in all_chunks
    ]

    qdrant.upsert(collection_name=collection_name, points=points)
    print(f"✅ {len(points)} vectors upserted into '{collection_name}'.")


if __name__ == "__main__":
    main()
