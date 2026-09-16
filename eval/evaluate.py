"""Step 7 — Testing & Evaluation.

Runs every question in eval/test_questions.json through the full RAG
pipeline for a given (embedding, retrieval strategy) combination, checks
whether the correct paper was retrieved, and uses Gemini itself as an
LLM-judge to score groundedness and relevance (a lightweight stand-in for
RAGAS / DeepEval, since those pull in a much heavier dependency tree for
what is fundamentally the same idea: "does the answer follow from the
context, and does it address the question").

Usage (from project root, with GEMINI_API_KEY set):
    python eval/evaluate.py --embedding huggingface --strategy hybrid

Resumable by design: a free-tier Gemini key can cap out at a handful of
requests *per day* (not just per minute), so results are written to
eval/results.csv after every question, and a re-run skips any (id,
embedding, strategy) row already present instead of re-spending quota.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.config import EVAL_DIR, GEMINI_API_KEY, GEMINI_LLM_MODEL, INDEX_DIR
from src.embeddings import get_embedder
from src.rag_chain import _invoke_with_backoff, generate_answer
from src.retrieval import RETRIEVAL_STRATEGIES
from src.vectorstore import BM25Index, load_faiss_index

# Free-tier Gemini keys have been observed as low as 5 requests/minute AND a
# hard daily cap (e.g. 20/day for a given model) on this project's own key.
# Two calls per question (answer + judge) means pacing matters even within
# the per-minute limit.
SECONDS_BETWEEN_QUESTIONS = 14

RESULTS_PATH = EVAL_DIR / "results.csv"

JUDGE_PROMPT = """You are grading a RAG system's answer. Score two things from 1 (worst) to 5 (best):

- groundedness: does every claim in the answer actually follow from the provided context \
(no invented facts)? A correct refusal ("I don't know...") when context is insufficient \
scores 5 for groundedness.
- relevance: does the answer actually address the question asked?

Question: {question}
Context provided to the model:
{context}

Model's answer: {answer}

Respond with ONLY a JSON object like {{"groundedness": <int>, "relevance": <int>}}.
"""


def _judge(question: str, context: str, answer: str) -> dict:
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(model=GEMINI_LLM_MODEL, google_api_key=GEMINI_API_KEY, temperature=0)
    result = _invoke_with_backoff(llm, JUDGE_PROMPT.format(question=question, context=context, answer=answer))
    text = result.content.strip().strip("`").replace("json", "", 1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"groundedness": None, "relevance": None}


def _load_existing() -> pd.DataFrame:
    if RESULTS_PATH.exists():
        return pd.read_csv(RESULTS_PATH)
    return pd.DataFrame()


def _save(df: pd.DataFrame) -> None:
    df.to_csv(RESULTS_PATH, index=False)


def run(embedding_name: str, strategy_name: str, k: int = 6, limit: int | None = None) -> pd.DataFrame:
    questions = json.loads((EVAL_DIR / "test_questions.json").read_text())
    if limit:
        questions = questions[:limit]

    existing = _load_existing()
    already_done = set()
    if not existing.empty:
        mask = (existing["embedding"] == embedding_name) & (existing["strategy"] == strategy_name)
        already_done = set(existing.loc[mask, "id"])
        if already_done:
            print(f"Resuming: {len(already_done)} question(s) already done for ({embedding_name}, {strategy_name}), skipping them.")

    embedder = get_embedder(embedding_name)
    vectorstore = load_faiss_index(INDEX_DIR / f"faiss_{embedding_name}", embedder)
    bm25 = BM25Index.load(INDEX_DIR / "bm25.pkl")
    retrieve_fn = RETRIEVAL_STRATEGIES[strategy_name]

    all_rows = existing.to_dict("records") if not existing.empty else []
    made_a_call = False

    for i, q in enumerate(questions):
        if q["id"] in already_done:
            continue

        if made_a_call and GEMINI_API_KEY:
            time.sleep(SECONDS_BETWEEN_QUESTIONS)

        print(f"[{i + 1}/{len(questions)}] {q['id']}: {q['question'][:70]}")
        retrieved = retrieve_fn(q["question"], vectorstore, bm25, k=k)
        retrieved_sources = {doc.metadata["source_file"] for doc, _ in retrieved}
        source_hit = (
            q["expected_source"] in retrieved_sources if q["expected_source"] else None
        )

        try:
            response = generate_answer(q["question"], retrieved, history=[])
            made_a_call = True
            context_text = "\n\n".join(doc.page_content for doc, _ in retrieved)

            judged = {"groundedness": None, "relevance": None}
            if GEMINI_API_KEY:
                judged = _judge(q["question"], context_text, response.answer)

            all_rows.append(
                {
                    "id": q["id"],
                    "type": q["type"],
                    "question": q["question"],
                    "expected_source": q["expected_source"],
                    "source_retrieved_correctly": source_hit,
                    "answer": response.answer,
                    "groundedness": judged.get("groundedness"),
                    "relevance": judged.get("relevance"),
                    "embedding": embedding_name,
                    "strategy": strategy_name,
                }
            )
            _save(pd.DataFrame(all_rows))
        except RuntimeError as e:
            print(f"\nStopped early on quota/rate-limit error: {e}")
            print(f"Progress saved to {RESULTS_PATH} — re-run the same command later to resume.")
            break

    return pd.DataFrame(all_rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--embedding", default="huggingface", choices=["huggingface", "gemini"])
    parser.add_argument("--strategy", default="hybrid", choices=list(RETRIEVAL_STRATEGIES.keys()))
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N questions (useful to conserve a tight daily quota).")
    args = parser.parse_args()

    if not GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY not set — running retrieval-only, skipping answer judging.")

    df = run(args.embedding, args.strategy, args.k, args.limit)
    subset = df[(df["embedding"] == args.embedding) & (df["strategy"] == args.strategy)]

    hit_rate = subset["source_retrieved_correctly"].dropna().mean() if subset["source_retrieved_correctly"].notna().any() else None
    print(f"\n{len(subset)}/{len(json.loads((EVAL_DIR / 'test_questions.json').read_text()))} questions completed for ({args.embedding}, {args.strategy}). Results in {RESULTS_PATH}")
    if hit_rate is not None:
        print(f"Retrieval hit rate (correct source in top-k): {hit_rate:.0%}")
    if subset["groundedness"].notna().any():
        print(f"Mean groundedness: {subset['groundedness'].mean():.2f}/5")
        print(f"Mean relevance:    {subset['relevance'].mean():.2f}/5")
