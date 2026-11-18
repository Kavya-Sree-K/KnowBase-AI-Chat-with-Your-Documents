"""
chunking.py - turn long page text into small, overlapping pieces.

Why chunk at all?
    A search over whole pages is too coarse, and an LLM prompt has limited
    room. Small chunks let us retrieve exactly the relevant paragraph.
"""

from __future__ import annotations

import re
from typing import List

from .config import CHUNK_OVERLAP, CHUNK_SIZE, MIN_CHUNK_WORDS

# Wikipedia exports contain headings like "== See also ==". They are noise
# for search, so we strip any line that is just "=== something ===".
_HEADING_RE = re.compile(r"^\s*=+\s*.*?\s*=+\s*$", re.MULTILINE)


def clean_text(text: str) -> str:
    """Remove wiki-style headings and collapse all whitespace."""
    text = _HEADING_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    min_words: int = MIN_CHUNK_WORDS,
) -> List[str]:
    """
    Slide a window of `chunk_size` words over the text.

    Neighbouring windows share `overlap` words so a sentence that falls on
    a boundary still appears whole in at least one chunk.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = clean_text(text).split()
    step = chunk_size - overlap
    chunks: List[str] = []

    for start in range(0, len(words), step):
        window = words[start:start + chunk_size]
        if len(window) >= min_words:      # skip tiny tails
            chunks.append(" ".join(window))
        if start + chunk_size >= len(words):  # reached the end of the text
            break
    return chunks
