"""Document loading and chunking.

Chunking happens per-page (not across the whole paper at once). That is a
deliberate trade-off: the capstone brief requires every chunk to carry an
accurate page number for citations, and splitting per page guarantees that —
at the cost of occasionally cutting a sentence that spans a page boundary.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


@dataclass
class Chunk:
    text: str
    paper_title: str
    source_file: str
    page: int
    chunk_id: str
    strategy: str = ""

    def to_metadata(self) -> dict:
        return {
            "paper_title": self.paper_title,
            "source_file": self.source_file,
            "page": self.page,
            "chunk_id": self.chunk_id,
            "strategy": self.strategy,
        }


def _display_title(filename: str) -> str:
    """Turn 'GPT3_Few_Shot_Learners.pdf' into 'GPT3 Few Shot Learners'."""
    stem = Path(filename).stem
    return re.sub(r"[_\-]+", " ", stem).strip()


def load_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """Return [(page_number_1_indexed, page_text), ...] for a PDF."""
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = re.sub(r"\s+\n", "\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        if text.strip():
            pages.append((i, text))
    return pages


def load_corpus(data_dir: Path) -> dict[str, list[tuple[int, str]]]:
    """Load every PDF in data_dir. Returns {filename: [(page, text), ...]}."""
    corpus = {}
    for pdf_path in sorted(data_dir.glob("*.pdf")):
        corpus[pdf_path.name] = load_pages(pdf_path)
    return corpus


# ---------------------------------------------------------------------------
# Chunking strategies
# ---------------------------------------------------------------------------

def chunk_fixed_size(
    corpus: dict[str, list[tuple[int, str]]], size: int = 900, overlap: int = 0
) -> list[Chunk]:
    """Naive fixed-size character windows, no overlap by default.

    Included mainly as the baseline to compare against — it frequently cuts
    sentences (and even words) mid-way, which shows up clearly once you read
    a few sample chunks in the notebook.
    """
    chunks: list[Chunk] = []
    for filename, pages in corpus.items():
        title = _display_title(filename)
        for page_num, text in pages:
            step = size - overlap if overlap < size else size
            for i, start in enumerate(range(0, len(text), step)):
                piece = text[start : start + size].strip()
                if len(piece) < 40:
                    continue
                chunks.append(
                    Chunk(
                        text=piece,
                        paper_title=title,
                        source_file=filename,
                        page=page_num,
                        chunk_id=f"{filename}:p{page_num}:fixed:{i}",
                        strategy="fixed_size",
                    )
                )
    return chunks


def chunk_recursive(
    corpus: dict[str, list[tuple[int, str]]], size: int = 900, overlap: int = 150
) -> list[Chunk]:
    """LangChain's RecursiveCharacterTextSplitter — splits on paragraph /
    sentence / word boundaries in that priority order, so chunks stay
    readable instead of being cut arbitrarily.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[Chunk] = []
    for filename, pages in corpus.items():
        title = _display_title(filename)
        for page_num, text in pages:
            pieces = splitter.split_text(text)
            for i, piece in enumerate(pieces):
                piece = piece.strip()
                if len(piece) < 40:
                    continue
                chunks.append(
                    Chunk(
                        text=piece,
                        paper_title=title,
                        source_file=filename,
                        page=page_num,
                        chunk_id=f"{filename}:p{page_num}:rec:{i}",
                        strategy="recursive",
                    )
                )
    return chunks


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def chunk_semantic(
    corpus: dict[str, list[tuple[int, str]]],
    embedder,
    similarity_drop_threshold: float = 0.28,
    max_chunk_chars: int = 1400,
) -> list[Chunk]:
    """Group consecutive sentences until the topic shifts.

    We embed each sentence, walk through them in order, and start a new
    chunk whenever cosine similarity to the previous sentence drops below
    `similarity_drop_threshold` (a proxy for a topic/section change), or the
    running chunk gets too long. This needs an embedding model up front —
    we use the small local HuggingFace model for this step regardless of
    which embedding model is later chosen for indexing, since it is free and
    fast enough to run per sentence.
    """
    import numpy as np

    chunks: list[Chunk] = []
    for filename, pages in corpus.items():
        title = _display_title(filename)
        for page_num, text in pages:
            sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
            if not sentences:
                continue
            if len(sentences) == 1:
                chunks.append(
                    Chunk(
                        text=sentences[0],
                        paper_title=title,
                        source_file=filename,
                        page=page_num,
                        chunk_id=f"{filename}:p{page_num}:sem:0",
                        strategy="semantic",
                    )
                )
                continue

            vectors = np.array(embedder.embed_documents(sentences))
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1e-8
            unit = vectors / norms

            current = [sentences[0]]
            chunk_idx = 0
            for i in range(1, len(sentences)):
                sim = float(np.dot(unit[i], unit[i - 1]))
                joined_len = sum(len(s) for s in current)
                if sim < similarity_drop_threshold or joined_len > max_chunk_chars:
                    piece = " ".join(current).strip()
                    if len(piece) >= 40:
                        chunks.append(
                            Chunk(
                                text=piece,
                                paper_title=title,
                                source_file=filename,
                                page=page_num,
                                chunk_id=f"{filename}:p{page_num}:sem:{chunk_idx}",
                                strategy="semantic",
                            )
                        )
                        chunk_idx += 1
                    current = [sentences[i]]
                else:
                    current.append(sentences[i])

            if current:
                piece = " ".join(current).strip()
                if len(piece) >= 40:
                    chunks.append(
                        Chunk(
                            text=piece,
                            paper_title=title,
                            source_file=filename,
                            page=page_num,
                            chunk_id=f"{filename}:p{page_num}:sem:{chunk_idx}",
                            strategy="semantic",
                        )
                    )
    return chunks


def sample_chunks(chunks: list[Chunk], per_paper: int = 10) -> list[Chunk]:
    """Evenly-spaced sample of chunks per paper.

    Used specifically for building the *commercial* (Gemini) embedding index:
    embedding the full ~1000-chunk corpus through a paid API just to run a
    side-by-side comparison against the free local model burns quota/cost
    for no real benefit. A representative sample is enough to compare
    embedding quality; the free HuggingFace index still covers the full
    corpus for actual production use in the app.
    """
    by_paper: dict[str, list[Chunk]] = {}
    for c in chunks:
        by_paper.setdefault(c.source_file, []).append(c)

    sampled: list[Chunk] = []
    for paper_chunks in by_paper.values():
        if len(paper_chunks) <= per_paper:
            sampled.extend(paper_chunks)
            continue
        step = len(paper_chunks) / per_paper
        sampled.extend(paper_chunks[int(i * step)] for i in range(per_paper))
    return sampled


CHUNKING_STRATEGIES = {
    "fixed_size": chunk_fixed_size,
    "recursive": chunk_recursive,
    "semantic": chunk_semantic,
}
