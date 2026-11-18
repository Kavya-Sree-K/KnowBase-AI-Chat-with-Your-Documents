"""
generators.py - turn retrieved passages into a final answer.

Three "answer engines" share the same inputs (question + passages):
    extractive -> no AI, just shows the best passages
    gemini     -> Google Gemini writes the answer
    claude     -> Anthropic Claude writes the answer
"""

from __future__ import annotations

from typing import List

from .config import CLAUDE_MAX_TOKENS, CLAUDE_MODEL, GEMINI_MODEL
from .knowledge_base import Passage


def build_prompt(query: str, hits: List[Passage]) -> str:
    """One prompt used by every LLM, so the behaviour stays consistent."""
    context = "\n\n".join(f"[p.{h.page}]: {h.text}" for h in hits)
    return (
        "You are a research assistant. Answer using ONLY the context below "
        "and cite page numbers like [p.5]. If the context is not enough, say so.\n\n"
        f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    )


def generate_extractive(query: str, hits: List[Passage]) -> str:
    """Fallback that needs no API key: show the top passages."""
    if not hits:
        return "Nothing relevant found in the PDF. Try rephrasing the question."
    body = "\n\n".join(
        f"**{h.title} (page {h.page}):** {h.text[:400]}..." for h in hits[:3]
    )
    return f"Based on the retrieved passages:\n\n{body}"


def generate_with_gemini(query: str, hits: List[Passage], api_key: str) -> str:
    # Imported here so the app still starts if this package is missing.
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    return model.generate_content(build_prompt(query, hits)).text


def generate_with_claude(query: str, hits: List[Passage], api_key: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        messages=[{"role": "user", "content": build_prompt(query, hits)}],
    )
    return message.content[0].text
