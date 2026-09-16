"""The RAG chain: prompt construction, LLM call, and citation formatting."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass

from langchain_core.documents import Document

from src.config import CITATIONS_SHOWN, GEMINI_API_KEY, GEMINI_LLM_MODEL

SYSTEM_PROMPT = """You are PaperMind, a research assistant that answers questions \
ONLY using the context passages provided below, which are excerpts from a curated \
set of GenAI research papers.

Rules:
1. Answer strictly from the given context. Do not use outside knowledge.
2. If the context does not contain enough information to answer, reply exactly: \
"I don't know based on the provided papers." Do not guess or fill gaps.
3. When you state a fact, keep it traceable to the context — write concisely, \
do not pad the answer with generic filler.
4. If the question is a casual follow-up (e.g. "explain that more simply"), use the \
conversation history to understand what "that" refers to, but still ground the \
answer in the context passages.
"""

ANSWER_PROMPT_TEMPLATE = """{system_prompt}

Conversation so far:
{history}

Context passages:
{context}

Question: {question}

Answer:"""

CONDENSE_PROMPT_TEMPLATE = """Given the conversation history and a follow-up question, \
rewrite the follow-up into a standalone question that contains all the context needed \
to answer it without seeing the history. If the follow-up is already standalone, return \
it unchanged. Return ONLY the rewritten question, nothing else.

Conversation history:
{history}

Follow-up question: {question}

Standalone question:"""


@dataclass
class Citation:
    rank: int
    paper_title: str
    page: int
    snippet: str
    score: float


@dataclass
class RAGResponse:
    answer: str
    citations: list[Citation]
    standalone_question: str


def _format_context(docs_scored: list[tuple[Document, float]]) -> str:
    blocks = []
    for i, (doc, score) in enumerate(docs_scored, start=1):
        meta = doc.metadata
        blocks.append(
            f"[Source {i}] {meta['paper_title']} (page {meta['page']})\n{doc.page_content}"
        )
    return "\n\n".join(blocks)


def _format_history(history: list[tuple[str, str]], max_turns: int = 4) -> str:
    if not history:
        return "(no previous turns)"
    recent = history[-max_turns:]
    lines = []
    for human, ai in recent:
        lines.append(f"User: {human}")
        lines.append(f"Assistant: {ai}")
    return "\n".join(lines)


def _get_llm():
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your .env file to generate answers."
        )
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=GEMINI_LLM_MODEL, google_api_key=GEMINI_API_KEY, temperature=0.1
    )


_RETRY_DELAY_RE = re.compile(r"retry in ([\d.]+)s")


def _invoke_with_backoff(llm, prompt: str, max_attempts: int = 4):
    """Retry on Gemini free-tier rate limits (as low as 5 requests/minute),
    honouring the server's suggested retry delay instead of a fixed one.

    langchain_google_genai's own built-in retry gives up too quickly for a
    quota this tight, so we handle it explicitly here rather than just
    letting a 429 surface as an unhandled exception mid-demo. Transient 5xx
    errors from Google's side (rare, but observed in practice) get a short
    fixed retry too, rather than being treated as a quota problem.
    """
    from google.api_core.exceptions import InternalServerError, ResourceExhausted, ServiceUnavailable

    last_error = None
    for attempt in range(max_attempts):
        try:
            return llm.invoke(prompt)
        except ResourceExhausted as e:
            last_error = e
            match = _RETRY_DELAY_RE.search(str(e))
            delay = float(match.group(1)) + 2 if match else 15.0
            if attempt < max_attempts - 1:
                time.sleep(delay)
        except (InternalServerError, ServiceUnavailable) as e:
            last_error = e
            if attempt < max_attempts - 1:
                time.sleep(5.0)
    raise RuntimeError(
        "Gemini API call failed repeatedly (rate limit or a transient server "
        "error). If it's quota: the free tier on this key allows very few "
        "requests/minute and/or a small daily cap — wait a bit or upgrade the "
        "key's quota in Google AI Studio / Cloud Console."
    ) from last_error


def condense_question(question: str, history: list[tuple[str, str]]) -> str:
    """Rewrite a follow-up question into a standalone one using chat history.

    This is the core of the conversational-memory stretch goal: without it, a
    follow-up like "what dataset did it use?" has no antecedent for "it" once
    it reaches the retriever.
    """
    if not history:
        return question
    llm = _get_llm()
    prompt = CONDENSE_PROMPT_TEMPLATE.format(
        history=_format_history(history), question=question
    )
    result = _invoke_with_backoff(llm, prompt)
    rewritten = result.content.strip().strip('"')
    return rewritten or question


def generate_answer(
    question: str,
    retrieved: list[tuple[Document, float]],
    history: list[tuple[str, str]] | None = None,
) -> RAGResponse:
    history = history or []
    llm = _get_llm()

    context = _format_context(retrieved)
    prompt = ANSWER_PROMPT_TEMPLATE.format(
        system_prompt=SYSTEM_PROMPT,
        history=_format_history(history),
        context=context,
        question=question,
    )
    result = _invoke_with_backoff(llm, prompt)
    answer_text = result.content.strip()

    citations = [
        Citation(
            rank=i,
            paper_title=doc.metadata["paper_title"],
            page=doc.metadata["page"],
            snippet=doc.page_content[:400],
            score=score,
        )
        for i, (doc, score) in enumerate(retrieved[:CITATIONS_SHOWN], start=1)
    ]

    return RAGResponse(answer=answer_text, citations=citations, standalone_question=question)
