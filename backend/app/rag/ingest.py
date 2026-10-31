"""
RAG Ingestion and Chunking Module.
Reads markdown files from knowledge/guidelines/, parses sections,
and generates structured chunks with stable chunk_ids and manifest metadata.
"""
import hashlib
import os
import re
from typing import Any, Dict, List
import yaml

KNOWLEDGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../knowledge"))
GUIDELINES_DIR = os.path.join(KNOWLEDGE_DIR, "guidelines")
MANIFEST_FILE = os.path.join(KNOWLEDGE_DIR, "manifest.yaml")


def load_manifest() -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(MANIFEST_FILE):
        return {}
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    docs = data.get("documents", [])
    return {doc["file_path"].split("/")[-1]: doc for doc in docs}


def chunk_document(file_name: str, content: str, doc_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Chunks document content by markdown headings (H1, H2, H3).
    Assigns stable chunk_ids based on file and section title hash.
    """
    chunks: List[Dict[str, Any]] = []
    # Split by markdown headers
    sections = re.split(r'\n(?=#{1,3}\s+)', content)

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        # Extract title from first line
        lines = sec.split("\n", 1)
        header_line = lines[0].strip()
        title = re.sub(r'^#{1,3}\s+', '', header_line)
        body = lines[1].strip() if len(lines) > 1 else ""

        # Skip headers with no body (e.g. solitary top-level title)
        if not body or len(body.split()) < 5:
            continue

        doc_id = doc_meta.get("id", file_name.replace(".md", ""))
        sec_slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')[:30]
        chunk_id = f"{doc_id}-{sec_slug}"

        full_chunk_text = f"{title}\n{body}".strip()

        chunks.append({
            "chunk_id": chunk_id,
            "document_id": doc_id,
            "document_title": doc_meta.get("title", title),
            "publisher": doc_meta.get("publisher", "Clinical Guidelines"),
            "year": doc_meta.get("year", 2023),
            "section_title": title,
            "text": full_chunk_text,
            "token_estimate": len(full_chunk_text.split()),
        })

    return chunks


def ingest_all_guidelines() -> List[Dict[str, Any]]:
    manifest = load_manifest()
    all_chunks = []

    if not os.path.exists(GUIDELINES_DIR):
        return all_chunks

    for fname in sorted(os.listdir(GUIDELINES_DIR)):
        if fname.endswith(".md"):
            fpath = os.path.join(GUIDELINES_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            doc_meta = manifest.get(fname, {})
            chunks = chunk_document(fname, content, doc_meta)
            all_chunks.extend(chunks)

    return all_chunks
