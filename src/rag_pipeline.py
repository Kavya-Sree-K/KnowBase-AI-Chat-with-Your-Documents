"""
rag_pipeline.py - the RAG recipe in one function:

    question -> retrieve passages -> generate answer -> return both
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from .config import TOP_K
from .generators import generate_extractive, generate_with_claude, generate_with_gemini
from .knowledge_base import KnowledgeBase, Passage

logger = logging.getLogger(__name__)


@dataclass
class RagResult:
    answer: str
    sources: List[Passage]
    provider_used: str   # may differ from the one requested if we fell back


def answer_question(
    query: str,
    kb: KnowledgeBase,
    provider: str = "extractive",
    api_key: str = "",
    top_k: int = TOP_K,
) -> RagResult:
    hits = kb.search(query, top_k=top_k)

    # Nothing retrieved -> no point paying for an LLM call.
    if not hits:
        return RagResult(generate_extractive(query, hits), [], "extractive")

    try:
        if provider == "gemini" and api_key:
            return RagResult(generate_with_gemini(query, hits, api_key), hits, "gemini")
        if provider == "claude" and api_key:
            return RagResult(generate_with_claude(query, hits, api_key), hits, "claude")
    except Exception as exc:  # network errors, bad key, quota, ...
        logger.warning("%s generation failed: %s", provider, exc)
        warning = f"⚠️ {provider} failed ({exc}). Showing extractive answer instead.\n\n"
        return RagResult(warning + generate_extractive(query, hits), hits, "extractive")

    # Either "extractive" was chosen or no API key was given.
    return RagResult(generate_extractive(query, hits), hits, "extractive")
