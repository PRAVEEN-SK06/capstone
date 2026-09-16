"""Embedding model factory.

Two models are supported end-to-end, per the capstone's compulsory
requirement to compare an open-source and a commercial embedding model:

* "huggingface" -> BAAI/bge-small-en-v1.5, runs 100% locally on CPU, free.
* "gemini"      -> Google's gemini-embedding-001, commercial API, needs a key.
"""
from __future__ import annotations

from functools import lru_cache

from src.config import EMBEDDING_MODELS, GEMINI_API_KEY


@lru_cache(maxsize=2)
def get_embedder(name: str):
    if name == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODELS["huggingface"],
            encode_kwargs={"normalize_embeddings": True},
        )

    if name == "gemini":
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file to use "
                "the Gemini embedding model."
            )
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODELS["gemini"], google_api_key=GEMINI_API_KEY
        )

    raise ValueError(f"Unknown embedding model '{name}'. Use 'huggingface' or 'gemini'.")


def available_embedders() -> list[str]:
    names = ["huggingface"]
    if GEMINI_API_KEY:
        names.append("gemini")
    return names
