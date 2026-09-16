"""Retrieval strategies compared in this project.

Each strategy is exposed as a function with the same signature so the
notebook / app can swap between them behind one interface:

    retrieve(query, vectorstore, bm25_index, k) -> list[(Document, score)]

Implemented:
* dense       - plain cosine similarity search over the FAISS index.
* mmr         - Maximal Marginal Relevance (relevance + diversity).
* hybrid      - Reciprocal Rank Fusion of BM25 (lexical) and dense ranks.
* hybrid_rerank - hybrid candidates re-scored by a cross-encoder reranker.
"""
from __future__ import annotations

from functools import lru_cache

from langchain_core.documents import Document

from src.vectorstore import BM25Index


def retrieve_dense(query: str, vectorstore, bm25_index: BM25Index, k: int = 6):
    results = vectorstore.similarity_search_with_relevance_scores(query, k=k)
    return [(doc, float(score)) for doc, score in results]


def retrieve_mmr(
    query: str, vectorstore, bm25_index: BM25Index, k: int = 6, fetch_k: int = 20, lambda_mult: float = 0.5
):
    docs = vectorstore.max_marginal_relevance_search(
        query, k=k, fetch_k=fetch_k, lambda_mult=lambda_mult
    )
    # MMR doesn't return scores; we surface rank position as a pseudo-score
    # (1.0 for the top result, decreasing) purely for display purposes.
    return [(doc, round(1.0 - i / max(len(docs), 1), 3)) for i, doc in enumerate(docs)]


def _reciprocal_rank_fusion(
    ranked_lists: list[list[str]], k_constant: int = 60
) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, key in enumerate(ranked):
            scores[key] = scores.get(key, 0.0) + 1.0 / (k_constant + rank + 1)
    return scores


def retrieve_hybrid(
    query: str, vectorstore, bm25_index: BM25Index, k: int = 6, candidate_pool: int = 20
):
    dense_results = vectorstore.similarity_search(query, k=candidate_pool)
    bm25_results = bm25_index.search(query, k=candidate_pool)

    dense_keys = [d.metadata["chunk_id"] for d in dense_results]
    bm25_keys = [c.chunk_id for c, _ in bm25_results]

    fused = _reciprocal_rank_fusion([dense_keys, bm25_keys])

    lookup: dict[str, Document] = {d.metadata["chunk_id"]: d for d in dense_results}
    for chunk, _ in bm25_results:
        if chunk.chunk_id not in lookup:
            lookup[chunk.chunk_id] = Document(page_content=chunk.text, metadata=chunk.to_metadata())

    ranked_keys = sorted(fused, key=lambda key: fused[key], reverse=True)[:k]
    return [(lookup[key], round(fused[key], 4)) for key in ranked_keys if key in lookup]


@lru_cache(maxsize=1)
def _get_reranker():
    from sentence_transformers import CrossEncoder

    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def retrieve_hybrid_rerank(
    query: str, vectorstore, bm25_index: BM25Index, k: int = 6, candidate_pool: int = 20
):
    """Hybrid retrieval followed by cross-encoder reranking of the pool.

    This is the highest-precision (and slowest) strategy: a small
    transformer scores every (query, candidate) pair directly instead of
    relying on pre-computed embedding similarity.
    """
    candidates = retrieve_hybrid(query, vectorstore, bm25_index, k=candidate_pool, candidate_pool=candidate_pool)
    if not candidates:
        return []
    reranker = _get_reranker()
    pairs = [[query, doc.page_content] for doc, _ in candidates]
    scores = reranker.predict(pairs)
    scored = list(zip([doc for doc, _ in candidates], scores))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [(doc, round(float(score), 4)) for doc, score in scored[:k]]


RETRIEVAL_STRATEGIES = {
    "dense": retrieve_dense,
    "mmr": retrieve_mmr,
    "hybrid": retrieve_hybrid,
    "hybrid_rerank": retrieve_hybrid_rerank,
}

STRATEGY_LABELS = {
    "dense": "Dense (cosine similarity)",
    "mmr": "MMR (relevance + diversity)",
    "hybrid": "Hybrid (BM25 + dense, RRF)",
    "hybrid_rerank": "Hybrid + cross-encoder reranker",
}
