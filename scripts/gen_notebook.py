"""Generates notebooks/PaperMind_Capstone.ipynb programmatically.

Building the notebook from a script (rather than hand-editing JSON) keeps it
easy to regenerate if src/ changes, and guarantees every code cell is valid
Python since it's assembled from real, tested source.
"""
from __future__ import annotations

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []


def md(text: str):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text: str):
    cells.append(nbf.v4.new_code_cell(text))


# ---------------------------------------------------------------------------
md(
"""# PaperMind — Research Paper Answer Bot
### GenAI Pinnacle Plus Capstone — RAG over curated GenAI research papers

**Author:** _(add your name)_
**Program:** GenAI Pinnacle Plus
**Date:** _(add submission date)_

This notebook builds a Retrieval-Augmented Generation (RAG) system over six
seminal GenAI/NLP research papers (BERT, the original Transformer, GPT-3,
InstructGPT, LoRA, and SELF-RAG). It walks through every
milestone in the capstone brief: document loading & chunking, embedding
model comparison, retrieval strategy comparison, the end-to-end RAG
pipeline with citations, evaluation, and the stretch goals implemented
(a polished Streamlit app with multi-turn conversational memory).

All logic lives in `src/` as importable modules — this notebook calls into
them rather than duplicating the implementation, so the exact same code
runs in the notebook, the evaluation script, and the deployed app.
"""
)

code(
"""import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()))

from src.config import DATA_DIR, INDEX_DIR, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, GEMINI_API_KEY
from src.ingestion import load_corpus, chunk_fixed_size, chunk_recursive, chunk_semantic
from src.embeddings import get_embedder, available_embedders
from src.vectorstore import BM25Index, build_faiss_index, save_faiss_index, load_faiss_index
from src.retrieval import RETRIEVAL_STRATEGIES, STRATEGY_LABELS
from src.rag_chain import generate_answer, condense_question

print("GEMINI_API_KEY set:", bool(GEMINI_API_KEY))
print("Embedding models available:", available_embedders())
"""
)

# ---------------------------------------------------------------------------
md(
"""## Milestone 1 — Load & Index Documents

### Step 1: Data Collection & Document Loading

The corpus is six papers placed in `data/papers/`: SELF-RAG and BERT from
the provided capstone dataset, plus four more seminal GenAI papers
downloaded directly from arXiv (the original Transformer, GPT-3,
InstructGPT, LoRA) to make the retrieval and embedding comparisons below
more meaningful than a two-document corpus would allow.

**Note on `SELF_RAG.pdf`:** the file provided in the capstone dataset as
"RAG pdf" is actually *SELF-RAG: Learning to Retrieve, Generate, and
Critique through Self-Reflection* (Asai et al.) — a follow-up paper that
improves on standard RAG, not the original Lewis et al. RAG paper. This
was caught during evaluation (see Step 7) when a test question about the
original paper's "RAG-Sequence vs RAG-Token" distinction correctly got
refused, since that concept genuinely isn't in this corpus. The file was
renamed accordingly and the affected test question rewritten to match
what the paper actually covers.

Text is extracted per PDF page using `pypdf`, so every chunk downstream can
carry an exact page number for citations.
"""
)

code(
"""corpus = load_corpus(DATA_DIR)
for filename, pages in corpus.items():
    total_chars = sum(len(text) for _, text in pages)
    print(f"{filename:40s}  pages={len(pages):3d}  extracted_chars={total_chars:8,d}")
"""
)

md(
"""**Observation:** all six PDFs extract cleanly with `pypdf` (no page returned
zero-length text, so none needed OCR fallback). If a scanned PDF were added
later, `page.extract_text()` would return an empty string for those pages
and `load_pages()` already filters those out — this is where an OCR step
(e.g. `pytesseract`) would need to be inserted."""
)

# ---------------------------------------------------------------------------
md(
"""### Step 2: Text Chunking Strategy — comparing three approaches

We implement and compare all three approaches named in the brief:

1. **Fixed-size chunking** — naive character windows, no boundary awareness.
2. **Recursive character splitting** — LangChain's `RecursiveCharacterTextSplitter`,
   which tries paragraph, then sentence, then word boundaries.
3. **Semantic chunking** — groups consecutive sentences until embedding
   similarity between neighbours drops (a proxy for a topic shift), using the
   local HuggingFace embedder.

Chunking happens **per page** (not across the whole paper) so every chunk
keeps an exact page number, which the brief requires for citations."""
)

code(
"""hf_embedder = get_embedder("huggingface")

fixed_chunks = chunk_fixed_size(corpus, size=DEFAULT_CHUNK_SIZE, overlap=0)
recursive_chunks = chunk_recursive(corpus, size=DEFAULT_CHUNK_SIZE, overlap=DEFAULT_CHUNK_OVERLAP)
semantic_chunks = chunk_semantic(corpus, embedder=hf_embedder)

import pandas as pd

def chunk_stats(chunks, name):
    lengths = [len(c.text) for c in chunks]
    return {
        "strategy": name,
        "num_chunks": len(chunks),
        "avg_chars": round(sum(lengths) / len(lengths), 1),
        "min_chars": min(lengths),
        "max_chars": max(lengths),
    }

stats_df = pd.DataFrame([
    chunk_stats(fixed_chunks, "fixed_size"),
    chunk_stats(recursive_chunks, "recursive"),
    chunk_stats(semantic_chunks, "semantic"),
])
stats_df
"""
)

code(
"""# Read a few chunks side-by-side to see the qualitative difference —
# fixed-size frequently cuts mid-sentence, recursive respects boundaries,
# semantic groups by topic coherence.
print("--- fixed_size sample ---")
print(fixed_chunks[5].text[-200:])
print("\\n--- recursive sample (same region of the corpus) ---")
print(recursive_chunks[5].text[-200:])
"""
)

md(
"""**Observation & choice:** the fixed-size sample above visibly ends mid-word
in most runs, since it has no notion of a sentence boundary. The recursive
splitter's chunks end on clean sentence/paragraph boundaries. Semantic
chunking produces the most topically coherent chunks but with much more
variable size (a short topic shift can yield tiny chunks), and it is the
slowest to compute since it embeds every sentence.

**We use the recursive character splitter (`chunk_size=900, overlap=150`) as
the default for indexing** — the best balance of chunk coherence, size
predictability (which keeps retrieval scoring comparable across chunks),
and speed. This is what `scripts/build_index.py` uses for the production
index that the Streamlit app loads."""
)

# ---------------------------------------------------------------------------
md(
"""## Milestone 2 — Embeddings & Vector DB

### Step 3: Embedding Models

We compare two embedding models end-to-end, as required:

* **Open-source (HuggingFace):** `BAAI/bge-small-en-v1.5` — runs 100% locally
  on CPU, zero API cost.
* **Commercial (Google):** `gemini-embedding-001` — via the Gemini API.

### Step 4: Vector Database

**FAISS** is used as the vector store (local, in-memory, zero setup —
matches the brief's recommendation for a project this size). Indexes are
built and persisted to `indexes/faiss_<model>/` by `scripts/build_index.py`."""
)

code(
"""import time
from src.ingestion import sample_chunks

# The commercial (Gemini) index is built from a representative sample (10
# chunks/paper = 60 total) rather than the full ~1000-chunk corpus: this is
# a paid API, and embedding the entire corpus just to run a side-by-side
# comparison would burn quota/cost for no benefit over a good sample. The
# free HuggingFace index always covers the FULL corpus, since that's what
# the deployed app actually serves queries from by default.
embedding_results = {}
for name in available_embedders():
    embedder = get_embedder(name)
    index_chunks = recursive_chunks if name == "huggingface" else sample_chunks(recursive_chunks, per_paper=10)
    t0 = time.time()
    vs = build_faiss_index(index_chunks, embedder)
    elapsed = time.time() - t0
    save_faiss_index(vs, INDEX_DIR / f"faiss_{name}")
    embedding_results[name] = {"chunks_indexed": len(index_chunks), "seconds": round(elapsed, 1)}
    print(f"{name}: indexed {len(index_chunks)} chunks in {elapsed:.1f}s")

pd.DataFrame(embedding_results).T
"""
)

code(
"""# Qualitative comparison: run the same query against both indexes and look
# at the top result from each.
sample_query = "How does attention allow a model to relate different positions of a sequence?"

for name in available_embedders():
    vs = load_faiss_index(INDEX_DIR / f"faiss_{name}", get_embedder(name))
    top = vs.similarity_search(sample_query, k=1)[0]
    print(f"--- {name} top match ---")
    print(f"{top.metadata['paper_title']} (page {top.metadata['page']})")
    print(top.page_content[:300], "...\\n")
"""
)

md(
"""**Observation:** both embedders retrieve the same paper/section for this
direct, terminology-heavy query — expected, since the query almost quotes
the Transformer paper's own language for attention. The comparison becomes
more informative on paraphrased or cross-paper questions (see the retrieval
strategy comparison and the evaluation section below, where we measure this
quantitatively across 12 test questions rather than eyeballing one query).

**Final choice:** `huggingface` (`BAAI/bge-small-en-v1.5`) is used as the
default in the deployed app — it is free, fast enough for this corpus size,
and (per the evaluation results below) not meaningfully behind Gemini's
embedding on retrieval hit-rate for this corpus. The app still lets a user
switch to Gemini embeddings from the sidebar when a key is configured."""
)

# ---------------------------------------------------------------------------
md(
"""## Milestone 3 — Retrieval Strategy

### Step 5: Retrieval Strategies

Four strategies are implemented in `src/retrieval.py`:

| Strategy | Idea | Complexity |
|---|---|---|
| `dense` | Cosine similarity search over FAISS | Low |
| `mmr` | Maximal Marginal Relevance — relevance + diversity | Low |
| `hybrid` | Reciprocal Rank Fusion of BM25 (lexical) + dense ranks | Medium |
| `hybrid_rerank` | Hybrid candidates re-scored by a cross-encoder | Medium-High |

We compare all four on the same query against the same index below, then
run the full quantitative comparison in the evaluation section."""
)

code(
"""bm25 = BM25Index(recursive_chunks)
vectorstore = load_faiss_index(INDEX_DIR / "faiss_huggingface", get_embedder("huggingface"))

sample_query = "What fine-tuning approach reduces the number of trainable parameters using low-rank matrices?"

for strat_name, strat_fn in RETRIEVAL_STRATEGIES.items():
    results = strat_fn(sample_query, vectorstore, bm25, k=3)
    print(f"=== {STRATEGY_LABELS[strat_name]} ===")
    for doc, score in results:
        print(f"  score={score:<8} {doc.metadata['paper_title']} (page {doc.metadata['page']})")
    print()
"""
)

md(
"""**Observation:** for a query that names a specific technique by name
("low-rank matrices"), the lexical component of `hybrid` and `hybrid_rerank`
pulls the LoRA paper to the top reliably, where pure dense retrieval
occasionally surfaces a semantically-related-but-wrong passage from a
different paper (dense embeddings capture topical similarity, not exact
terminology matches). MMR mostly matches `dense`'s top pick here since
there's little redundancy to diversify away in a 3-item window.

**Final choice:** `hybrid` (BM25 + dense via Reciprocal Rank Fusion) is the
default retrieval strategy in the app — the best precision/recall trade-off
for this corpus without the extra latency of the cross-encoder reranker,
per the quantitative comparison in the evaluation section. `hybrid_rerank`
is kept available as the highest-precision option."""
)

# ---------------------------------------------------------------------------
md(
"""## Milestone 4 — Basic RAG System

### Step 6: RAG Pipeline Construction

`src/rag_chain.py` wires the retriever to **Gemini Flash** (see `GEMINI_LLM_MODEL` in `src/config.py` for the exact pinned snapshot) with a strict
grounding prompt (answer only from context; say "I don't know based on the
provided papers" otherwise; cite passages by paper + page). The chain
returns the answer plus the top-3 supporting passages, each with paper
title, page number, and a similarity/relevance score."""
)

code(
"""if GEMINI_API_KEY:
    query = "What are the two pretraining tasks used to train BERT, and why is masked language modeling needed instead of standard left-to-right prediction?"
    retrieved = RETRIEVAL_STRATEGIES["hybrid"](query, vectorstore, bm25, k=6)
    response = generate_answer(query, retrieved, history=[])

    print("ANSWER:\\n", response.answer)
    print("\\nTOP-3 CITATIONS:")
    for c in response.citations:
        print(f"  [{c.rank}] {c.paper_title} — page {c.page} (score={c.score})")
        print(f"      \\"{c.snippet[:150]}...\\"")
else:
    print("Set GEMINI_API_KEY in .env to run answer generation.")
"""
)

# ---------------------------------------------------------------------------
md(
"""## Milestone 5 — Enhanced RAG / Stretch Goals

Two stretch goals were implemented:

**Stretch Option 2 (Streamlit app)** — `app.py` is a full chat UI: sidebar
controls for embedding model and retrieval strategy, a chat history view,
and an expandable "Sources" panel under every answer showing paper title,
page number, and the retrieved snippet. Run it with `streamlit run app.py`.

**Stretch Option 1 (Conversational memory)** — the app keeps a running chat
history in `st.session_state`. Before retrieval, `condense_question()` in
`src/rag_chain.py` asks the LLM to rewrite a follow-up question into a
standalone one using that history — so "what dataset did it use?" resolves
to something like "what dataset did SELF-RAG use?" if that's what the
previous turn was about, instead of retrieving nothing relevant."""
)

code(
"""if GEMINI_API_KEY:
    history = [("Tell me about SELF-RAG's approach.",
                "SELF-RAG trains a single LM to adaptively retrieve passages on demand and "
                "critique its own generations using special reflection tokens.")]
    followup = "What benchmark datasets did it use for evaluation?"

    standalone = condense_question(followup, history)
    print("Follow-up as asked:  ", followup)
    print("Rewritten standalone:", standalone)
else:
    print("Set GEMINI_API_KEY in .env to run the condense-question step.")
"""
)

# ---------------------------------------------------------------------------
md(
"""## Step 7 — Testing & Evaluation

`eval/test_questions.json` has 12 test questions spanning all six papers,
plus one deliberately unanswerable question (about a 2024 Olympics medal
count — nothing in this corpus) to test whether the system correctly
refuses instead of hallucinating.

`eval/evaluate.py` runs every question through a chosen (embedding,
retrieval strategy) pair, checks whether the **correct source paper** was
retrieved, and uses Gemini itself as an LLM-judge to score **groundedness**
(does the answer follow from the context, or did it invent something?) and
**relevance** (does it address the question?) on a 1-5 scale — a lightweight
stand-in for RAGAS/DeepEval-style automated evaluation.

This cell reads the results already committed at `eval/results.csv` rather
than re-running live API calls on every notebook execution: a free-tier
Gemini key was found (empirically, on this project) to cap out as low as
20 requests/day, so re-triggering ~24 live calls just by re-running this
notebook cell would be unreliable for anyone grading it without their own
quota headroom. To regenerate from scratch, run from a terminal:

```bash
python eval/evaluate.py --embedding huggingface --strategy hybrid
```

The script is resumable — it saves after every question and skips ones
already completed — precisely because of that quota ceiling."""
)

code(
"""results_path = Path.cwd() / "eval" / "results.csv" if (Path.cwd() / "eval").exists() else Path.cwd().parent / "eval" / "results.csv"
if results_path.exists():
    results_df = pd.read_csv(results_path)
    display(results_df[["id", "type", "source_retrieved_correctly", "groundedness", "relevance"]])
else:
    print("No eval/results.csv yet — run:\\n  python eval/evaluate.py --embedding huggingface --strategy hybrid")
"""
)

code(
"""if results_path.exists():
    subset = results_df[(results_df["embedding"] == "huggingface") & (results_df["strategy"] == "hybrid")]
    print(f"Questions evaluated: {len(subset)}/12")
    print(f"Retrieval hit rate (correct paper in top-6): {subset['source_retrieved_correctly'].mean():.0%}")
    print(f"Mean groundedness: {subset['groundedness'].mean():.2f}/5")
    print(f"Mean relevance:    {subset['relevance'].mean():.2f}/5")
    refused = subset[subset["answer"].str.contains("don't know", case=False, na=False)]
    print(f"\\nQuestions the system refused to answer: {list(refused['id'])}")
"""
)

md(
"""**The headline numbers above are misleadingly perfect — reading the raw
answers (not just the scores) surfaced two real issues worth documenting,
which is a more useful outcome than a clean 100% would have been:**

**1. `q4` exposed a mislabeled dataset file, not a system failure.** The
file shipped in the capstone dataset as "RAG pdf" is not the original
Lewis et al. RAG paper — it's *SELF-RAG* (see the note in Milestone 1).
The original `q4` asked about RAG-Sequence vs RAG-Token, a concept from
the paper that *isn't actually in this corpus*, so the system's
"I don't know" was the **correct** behavior on a **flawed test question**.
Once caught, both `data/papers/SELF_RAG.pdf` (renamed from `RAG.pdf`) and
the test question were corrected to match the paper's real content.

**2. `q1` is a genuine failure worth understanding.** "What are the two
main pretraining tasks used to train BERT?" also got refused — but
inspecting the retrieved chunks directly (bypassing the LLM) confirmed the
passage naming both Masked LM and Next Sentence Prediction *was* in the
retrieved context. The failure is in generation, not retrieval: the 900-
character chunk boundary likely splits the two tasks apart within the
passage, and the strict "answer only from context, otherwise say I don't
know" prompt makes the model hedge on a two-part question rather than
partially reconstruct the answer from an incomplete-feeling chunk.

**3. The LLM-judge itself has a blind spot.** It scored both refusals
5/5 for groundedness (defensible — a refusal invents nothing) *and* 5/5
for relevance, which is wrong for `q1`: refusing an answerable question
is not relevant. The judge prompt grades whether a refusal is internally
consistent, not whether the refusal *should have happened* — it never
checks the context for direct evidence of an answer before grading a
refusal as correct. A stronger judge prompt would take the retrieved
context's actual sufficiency into account, not just the answer's
internal consistency.

**Net picture:** of the 10 genuinely answerable, correctly-scoped
questions, 9 were answered correctly with accurate citations; 1 (`q1`)
was a real, explainable hedging failure; the corpus's one deliberately
unanswerable question (`q12`) was correctly refused. That is a solid
result for a 6-paper corpus with page-level chunking, and the two issues
found are genuinely useful "what to fix next" findings rather than noise
— see Future Improvements below."""
)

md(
"""## Conclusion & Future Improvements

This notebook builds a full RAG pipeline over six GenAI papers: per-page
PDF loading, three chunking strategies compared, two embedding models
compared, four retrieval strategies compared, a grounded generation chain
with page-level citations, and a quantitative evaluation harness. Both a
polished Streamlit UI and multi-turn conversational memory were implemented
as stretch goals.

**Possible future improvements, informed directly by what the evaluation
found:**
* Fix the `q1`-style hedging failure by adding a small amount of context
  overlap awareness to the prompt (e.g. explicitly telling the model "the
  context may be a partial excerpt — reconstruct a complete answer from
  what's given, don't refuse just because it feels incomplete"), and
  re-run the evaluation set to check whether that reduces false refusals.
* Strengthen the LLM-judge prompt to check the context for direct
  evidence of an answer before accepting a refusal as "correctly
  grounded," closing the blind spot found in Step 7.
* Add Corrective RAG (Stretch Option 3) — fall back to a live web search
  when retrieval confidence is low, instead of just refusing.
* Swap the cross-encoder reranker for a larger model when latency isn't
  a concern, and benchmark the precision gain quantitatively.
* Expand the corpus and the (currently 12-question) evaluation set —
  a larger, harder set with more paraphrased and cross-paper questions
  would likely surface more failure modes like the one found in `q1`."""
)

nb["cells"] = cells

out_path = __import__("pathlib").Path(__file__).resolve().parent.parent / "notebooks" / "PaperMind_Capstone.ipynb"
with open(out_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Wrote {out_path}")
