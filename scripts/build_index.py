"""Build the production FAISS + BM25 indexes used by the Streamlit app.

Run from the project root:
    python scripts/build_index.py

Builds one FAISS index per available embedding model (HuggingFace always,
Gemini only if GEMINI_API_KEY is set) using the chunking strategy chosen in
notebooks/PaperMind_Capstone.ipynb (recursive character splitting — see the
notebook's Milestone 3 section for the comparison that justifies this).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_DIR, DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, INDEX_DIR
from src.embeddings import available_embedders, get_embedder
from src.ingestion import chunk_recursive, load_corpus, sample_chunks
from src.vectorstore import BM25Index, build_faiss_index, save_faiss_index


def main():
    print(f"Loading PDFs from {DATA_DIR} ...")
    corpus = load_corpus(DATA_DIR)
    if not corpus:
        print("No PDFs found in data/papers/. Add some and re-run.")
        return
    for filename, pages in corpus.items():
        print(f"  - {filename}: {len(pages)} pages with extractable text")

    print(f"\nChunking (recursive splitter, size={DEFAULT_CHUNK_SIZE}, overlap={DEFAULT_CHUNK_OVERLAP}) ...")
    chunks = chunk_recursive(corpus, size=DEFAULT_CHUNK_SIZE, overlap=DEFAULT_CHUNK_OVERLAP)
    print(f"  -> {len(chunks)} chunks")

    print("\nBuilding BM25 lexical index ...")
    bm25 = BM25Index(chunks)
    bm25.save(INDEX_DIR / "bm25.pkl")
    print(f"  -> saved to {INDEX_DIR / 'bm25.pkl'}")

    for name in available_embedders():
        # The commercial (Gemini) index is built from a representative sample,
        # not the full corpus — see src/ingestion.sample_chunks for why. The
        # free local HuggingFace index always covers the full corpus, since
        # that's what the app actually serves queries from by default.
        index_chunks = chunks if name == "huggingface" else sample_chunks(chunks, per_paper=10)
        print(f"\nBuilding FAISS index with '{name}' embeddings ({len(index_chunks)} chunks) ...")
        t0 = time.time()
        embedder = get_embedder(name)
        index = build_faiss_index(index_chunks, embedder)
        save_faiss_index(index, INDEX_DIR / f"faiss_{name}")
        print(f"  -> saved to {INDEX_DIR / f'faiss_{name}'} ({time.time() - t0:.1f}s)")

    print("\nDone. Run `streamlit run app.py` to launch the app.")


if __name__ == "__main__":
    main()
