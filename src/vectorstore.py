"""Vector store (FAISS) and lexical index (BM25) construction / persistence."""
from __future__ import annotations

import pickle
import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi

from src.ingestion import Chunk

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def chunks_to_documents(chunks: list[Chunk]) -> list[Document]:
    return [Document(page_content=c.text, metadata=c.to_metadata()) for c in chunks]


def build_faiss_index(chunks: list[Chunk], embedder) -> FAISS:
    docs = chunks_to_documents(chunks)
    return FAISS.from_documents(docs, embedder)


def save_faiss_index(index: FAISS, path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    index.save_local(str(path))


def load_faiss_index(path: Path, embedder) -> FAISS:
    return FAISS.load_local(
        str(path), embedder, allow_dangerous_deserialization=True
    )


class BM25Index:
    """Thin wrapper pairing a BM25Okapi model with the chunk list it indexes,
    so scores can be mapped back to (text, metadata) pairs.
    """

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self._corpus_tokens = [_tokenize(c.text) for c in chunks]
        self._bm25 = BM25Okapi(self._corpus_tokens)

    def search(self, query: str, k: int = 10) -> list[tuple[Chunk, float]]:
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [(self.chunks[i], float(scores[i])) for i in ranked]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self.chunks, f)

    @classmethod
    def load(cls, path: Path) -> "BM25Index":
        with open(path, "rb") as f:
            chunks = pickle.load(f)
        return cls(chunks)
