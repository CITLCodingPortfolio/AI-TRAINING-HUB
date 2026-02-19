from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
def _read_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    chunks = []
    for page in reader.pages:
        t = page.extract_text() or ""
        chunks.append(t)
    return "\n".join(chunks)
def simple_chunk(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    text = text.replace("\r", "\n")
    s = " ".join(text.split())
    out = []
    i = 0
    while i < len(s):
        out.append(s[i:i+chunk_size])
        i += max(1, chunk_size - overlap)
    return out
class RagStore:
    def __init__(self, persist_dir: Path, embed_model: str = "all-MiniLM-L6-v2"):
        self.persist_dir = persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        self.embedder = SentenceTransformer(embed_model)
    def ingest_files(self, collection: str, files: List[Path]) -> Dict[str, Any]:
        col = self.client.get_or_create_collection(collection)
        added = 0
        for f in files:
            if f.suffix.lower() == ".pdf":
                text = _read_pdf_text(f)
            else:
                text = f.read_text(encoding="utf-8", errors="ignore")
            chunks = simple_chunk(text)
            if not chunks:
                continue
            embeds = self.embedder.encode(chunks, normalize_embeddings=True).tolist()
            ids = [f"{f.name}-{i}" for i in range(len(chunks))]
            metas = [{"source": f.name, "chunk": i} for i in range(len(chunks))]
            col.add(ids=ids, documents=chunks, embeddings=embeds, metadatas=metas)
            added += len(chunks)
        return {"collection": collection, "chunks_added": added}
    def query(self, collection: str, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        col = self.client.get_or_create_collection(collection)
        qemb = self.embedder.encode([query_text], normalize_embeddings=True).tolist()
        res = col.query(query_embeddings=qemb, n_results=top_k, include=["documents", "metadatas", "distances"])
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        out = []
        for doc, meta, dist in zip(docs, metas, dists):
            out.append({"text": doc, "meta": meta, "distance": dist})
        return out
