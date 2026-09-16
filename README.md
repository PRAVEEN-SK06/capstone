# \U0001F9E0 PaperMind — Research Paper Answer Bot

A Retrieval-Augmented Generation (RAG) system for asking questions over a
curated set of seminal GenAI research papers (BERT, the original
Transformer, GPT-3, InstructGPT, LoRA, and SELF-RAG), built as
a GenAI Pinnacle Plus capstone project.

Every answer is generated **strictly from retrieved passages**, with the
top-3 supporting sources (paper title + page number) shown alongside it, so
answers stay verifiable instead of relying on the model's own memory.

## What's implemented

**Compulsory goals** (see `notebooks/PaperMind_Capstone.ipynb` for the full
walkthrough and comparisons):
- PDF loading & per-page text extraction (`src/ingestion.py`)
- 3 chunking strategies compared: fixed-size, recursive character splitting, semantic chunking
- 2 embedding models compared: HuggingFace `BAAI/bge-small-en-v1.5` (local, free) and Google `gemini-embedding-001` (commercial)
- 4 retrieval strategies compared: dense cosine, MMR, hybrid (BM25 + dense via reciprocal rank fusion), hybrid + cross-encoder reranker
- Full RAG pipeline (Gemini Flash, see `src/config.py` for the exact pinned snapshot) returning top-3 cited passages with paper title + page number
- Evaluation harness over 12 test questions, including an LLM-as-judge groundedness/relevance score and one deliberately unanswerable question to test hallucination refusal

**Stretch goals implemented:**
- **Option 2 (Streamlit app)** — `app.py`, a full chat UI with sidebar controls for embedding model / retrieval strategy / top-k, and an expandable "Sources" panel per answer.
- **Option 1 (Conversational memory)** — multi-turn chat history with an LLM-based "condense question" step so follow-ups like "what dataset did it use?" resolve correctly before retrieval.

## Project structure

```
app.py                      Streamlit chat UI
src/
  config.py                 Paths, model names, defaults
  ingestion.py               PDF loading + 3 chunking strategies
  embeddings.py              Embedding model factory (HuggingFace / Gemini)
  vectorstore.py              FAISS index + BM25 lexical index
  retrieval.py                4 retrieval strategies
  rag_chain.py                Prompting, generation, citations, conversational memory
scripts/
  build_index.py              Builds the production FAISS + BM25 indexes
  gen_notebook.py              Generates notebooks/PaperMind_Capstone.ipynb from src/
eval/
  test_questions.json          12 test questions
  evaluate.py                   Retrieval-hit-rate + LLM-judge evaluation
notebooks/
  PaperMind_Capstone.ipynb      Primary submission notebook (all milestones)
data/papers/                    The 6-paper PDF corpus
indexes/                        Persisted FAISS + BM25 indexes (huggingface index is committed; gemini index is not)
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your Gemini API key (free at
[aistudio.google.com/apikey](https://aistudio.google.com/apikey)):

```
GEMINI_API_KEY=your_key_here
```

Build the indexes (only needed once, or after changing the corpus/chunking):

```bash
python scripts/build_index.py
```

Run the app:

```bash
streamlit run app.py
```

Run the evaluation harness:

```bash
python eval/evaluate.py --embedding huggingface --strategy hybrid
```

Regenerate the notebook after changing `src/` (needs the extra dev dependencies):

```bash
pip install -r requirements-dev.txt
python scripts/gen_notebook.py
```

## Design decisions worth knowing for the viva

- **Chunking happens per PDF page**, not across the whole document. This
  guarantees every chunk carries an exact page number for citations, at the
  cost of occasionally splitting a sentence across a page boundary.
- **Retrieval strategies are compared via Reciprocal Rank Fusion** for the
  hybrid strategy rather than a hand-tuned weighted sum of BM25 and dense
  scores — RRF needs no score normalization between the two very
  different scales BM25 and cosine similarity produce.
- **The system prompt hard-codes a refusal string** ("I don't know based on
  the provided papers.") specifically to make hallucination-refusal
  measurable in the evaluation harness, rather than leaving refusal
  phrasing to the model's own judgment.
- **The HuggingFace embedding index is committed to the repo**; the Gemini
  index is not (gitignored), since it depends on a paid API key and isn't
  needed for the app to run out of the box — the app builds it on first use
  if a key is present.

## Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub (see below).
2. Go to [share.streamlit.io](https://share.streamlit.io), connect the repo, set the main file to `app.py`.
3. In the app's "Secrets" settings, add:
   ```toml
   GEMINI_API_KEY = "your_key_here"
   ```
4. Deploy. The committed `indexes/faiss_huggingface/` and `indexes/bm25.pkl` mean the app is queryable immediately — no index build needed on first load.

## Known limitations

- **Free-tier Gemini rate limit:** a freshly created Gemini API key can be
  capped at as little as **5 requests/minute**, shared across the LLM and any
  Gemini-embedding calls. `src/rag_chain.py` retries with backoff honouring
  the server's suggested delay, and the app shows a clear warning instead of
  crashing if the quota is exhausted — but for a smooth live demo, pace
  questions roughly 15-20 seconds apart, or request a quota increase for the
  key in Google AI Studio / Cloud Console beforehand.
- Model names on Google's side move fairly often (see the comment above
  `GEMINI_LLM_MODEL` in `src/config.py`) — if a model 404s with "no longer
  available", run `python scripts/list_gemini_models.py` to see current
  options for your key.

## Tech stack

Streamlit • LangChain • FAISS • rank_bm25 • sentence-transformers (embeddings + cross-encoder reranker) • Google Gemini (LLM + commercial embeddings) • pypdf
