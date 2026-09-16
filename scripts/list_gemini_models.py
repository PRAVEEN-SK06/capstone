"""Lists Gemini models your API key currently has access to.

Model availability changes over time (older snapshots get retired for new
keys/projects), so if src/config.py's GEMINI_LLM_MODEL or the embedding
model name ever starts 404ing, run this to see current options:

    python scripts/list_gemini_models.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import google.generativeai as genai

from src.config import GEMINI_API_KEY

if not GEMINI_API_KEY:
    raise SystemExit("Set GEMINI_API_KEY in .env first.")

genai.configure(api_key=GEMINI_API_KEY)

print("Chat/generation models:")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(f"  {m.name}")

print("\nEmbedding models:")
for m in genai.list_models():
    if "embedContent" in m.supported_generation_methods:
        print(f"  {m.name}")
