"""Central configuration for PaperMind.

Values here are deliberately simple constants (not a settings framework) since
the whole project is a single capstone app, not a multi-environment service.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "papers"
INDEX_DIR = ROOT_DIR / "indexes"
EVAL_DIR = ROOT_DIR / "eval"

INDEX_DIR.mkdir(parents=True, exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Embedding models available in the app / notebook.
EMBEDDING_MODELS = {
    "huggingface": "BAAI/bge-small-en-v1.5",
    "gemini": "models/gemini-embedding-001",
}

# LLM used for answer generation and for the conversational "condense question" step.
# Free-tier Gemini quota is scoped per (project, model) and can be as low as
# 20 requests/day on some models (observed directly on this project's key) —
# if this model 404s ("no longer available") or 429s with quota exhausted,
# run `python scripts/list_gemini_models.py` and try a different current
# model name; different models draw from separate quota buckets.
GEMINI_LLM_MODEL = "gemini-3.1-flash-lite"

# Chunking defaults (the notebook experiments with alternatives; this is the
# value chosen after that comparison — see notebooks/PaperMind_Capstone.ipynb).
DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 150

# Retrieval defaults.
DEFAULT_TOP_K = 6
CITATIONS_SHOWN = 3
