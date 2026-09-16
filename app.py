"""PaperMind — Research Paper Answer Bot.

Streamlit UI on top of the RAG pipeline in src/. Covers Stretch Goal 2
(polished Streamlit app) and Stretch Goal 1 (multi-turn conversational RAG
with chat history / question condensing).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from src.config import DATA_DIR, GEMINI_API_KEY, INDEX_DIR
from src.embeddings import available_embedders, get_embedder
from src.ingestion import chunk_recursive, load_corpus, sample_chunks
from src.rag_chain import condense_question, generate_answer
from src.retrieval import RETRIEVAL_STRATEGIES, STRATEGY_LABELS
from src.vectorstore import BM25Index, build_faiss_index, load_faiss_index, save_faiss_index

st.set_page_config(page_title="PaperMind", page_icon="\U0001F9E0", layout="wide")


@st.cache_resource(show_spinner=False)
def _load_bm25() -> BM25Index:
    path = INDEX_DIR / "bm25.pkl"
    if not path.exists():
        _build_indexes_from_scratch()
    return BM25Index.load(path)


@st.cache_resource(show_spinner="Loading vector index...")
def _load_vectorstore(embedding_name: str):
    path = INDEX_DIR / f"faiss_{embedding_name}"
    embedder = get_embedder(embedding_name)
    if not path.exists():
        if embedding_name == "huggingface":
            _build_indexes_from_scratch()
        else:
            # Built from a representative sample, not the full corpus, so
            # picking Gemini embeddings in the sidebar doesn't silently fire
            # ~1000 paid embedding calls — see src/ingestion.sample_chunks.
            corpus = load_corpus(DATA_DIR)
            chunks = sample_chunks(chunk_recursive(corpus), per_paper=10)
            index = build_faiss_index(chunks, embedder)
            save_faiss_index(index, path)
    return load_faiss_index(path, embedder)


def _build_indexes_from_scratch():
    from scripts.build_index import main as build_main

    build_main()


def _paper_list() -> list[str]:
    return sorted(p.stem.replace("_", " ") for p in DATA_DIR.glob("*.pdf"))


# --- Sidebar -----------------------------------------------------------
with st.sidebar:
    st.title("\U0001F9E0 PaperMind")
    st.caption("Research Paper Answer Bot — RAG over GenAI papers")

    st.subheader("Corpus")
    for title in _paper_list():
        st.markdown(f"- {title}")

    st.subheader("Embedding model")
    embed_options = available_embedders()
    embed_labels = {"huggingface": "HuggingFace (BAAI/bge-small, local, free)", "gemini": "Gemini (gemini-embedding-001, commercial)"}
    embedding_name = st.radio(
        "Embedding model",
        embed_options,
        format_func=lambda x: embed_labels.get(x, x),
        label_visibility="collapsed",
    )
    if "gemini" not in embed_options:
        st.caption("Set GEMINI_API_KEY in .env to also compare the commercial embedding model.")

    st.subheader("Retrieval strategy")
    strategy_name = st.radio(
        "Retrieval strategy",
        list(RETRIEVAL_STRATEGIES.keys()),
        format_func=lambda x: STRATEGY_LABELS[x],
        index=2,
        label_visibility="collapsed",
    )

    top_k = st.slider("Passages to retrieve (k)", min_value=3, max_value=10, value=6)

    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

if not GEMINI_API_KEY:
    st.warning(
        "**GEMINI_API_KEY is not set.** Retrieval will work, but answer generation needs "
        "a Gemini key. Copy `.env.example` to `.env` and add your key, then restart the app.",
        icon="⚠️",
    )

st.title("\U0001F9E0 PaperMind — Research Paper Answer Bot")
st.caption(
    "Ask a question about the indexed research papers. Answers are generated strictly "
    "from retrieved passages, with the top supporting sources shown below each answer."
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of (question, answer)
if "display_history" not in st.session_state:
    st.session_state.display_history = []  # list of dicts for rendering (incl. citations)

for turn in st.session_state.display_history:
    with st.chat_message("user"):
        st.markdown(turn["question"])
    with st.chat_message("assistant"):
        st.markdown(turn["answer"])
        if turn["citations"]:
            with st.expander(f"\U0001F4DA Sources ({len(turn['citations'])})"):
                for c in turn["citations"]:
                    st.markdown(f"**[{c.rank}] {c.paper_title} — page {c.page}**  \n_score: {c.score}_")
                    st.markdown(f"> {c.snippet}...")

query = st.chat_input("Ask about the papers, e.g. 'How does RAG combine retrieval with generation?'")

if query:
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving relevant passages..."):
            bm25 = _load_bm25()
            vectorstore = _load_vectorstore(embedding_name)
            standalone_q = condense_question(query, st.session_state.chat_history) if GEMINI_API_KEY else query
            retrieve_fn = RETRIEVAL_STRATEGIES[strategy_name]
            retrieved = retrieve_fn(standalone_q, vectorstore, bm25, k=top_k)

        if not GEMINI_API_KEY:
            answer_text = (
                "Retrieval-only mode (no GEMINI_API_KEY set). Top passages retrieved for "
                f"*\"{standalone_q}\"* are shown in Sources below."
            )
            citations = [
                type("C", (), {"rank": i, "paper_title": d.metadata["paper_title"], "page": d.metadata["page"], "snippet": d.page_content[:400], "score": s})()
                for i, (d, s) in enumerate(retrieved[:3], start=1)
            ]
            st.markdown(answer_text)
        else:
            try:
                with st.spinner("Generating grounded answer... (the free-tier Gemini key on this project allows only a few requests/minute, so this can take a moment)"):
                    response = generate_answer(standalone_q, retrieved, st.session_state.chat_history)
                answer_text = response.answer
                citations = response.citations
                st.markdown(answer_text)
                st.session_state.chat_history.append((query, answer_text))
            except RuntimeError as e:
                answer_text = f"⚠️ {e}"
                citations = []
                st.error(answer_text)

        if citations:
            with st.expander(f"\U0001F4DA Sources ({len(citations)})"):
                for c in citations:
                    st.markdown(f"**[{c.rank}] {c.paper_title} — page {c.page}**  \n_score: {c.score}_")
                    st.markdown(f"> {c.snippet}...")

    st.session_state.display_history.append(
        {"question": query, "answer": answer_text, "citations": citations}
    )
