"""
knowledge_base.py - a tiny search index built with TF-IDF.

TF-IDF turns every chunk into a vector of word weights. A question is turned
into a vector the same way, and cosine similarity tells us which chunks
look most like the question. No GPU, no API, no embeddings model needed.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .chunking import split_into_chunks
from .config import CHUNK_OVERLAP, CHUNK_SIZE, MAX_FEATURES, TOP_K
from .pdf_loader import PageText


@dataclass(frozen=True)
class Passage:
    """One searchable chunk plus where it came from."""
    text: str
    title: str
    page: int
    score: float = 0.0   # filled in by search(): 0 (no match) .. 1 (identical)


class KnowledgeBase:
    def __init__(self) -> None:
        self.passages: List[Passage] = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._matrix = None  # sparse matrix: one row per passage

    # ---------- building the index ----------
    def add_pages(
        self,
        pages: List[PageText],
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,
    ) -> None:
        """Chunk every page, store the chunks, then (re)build the index."""
        for page in pages:
            for piece in split_into_chunks(page.text, chunk_size, overlap):
                self.passages.append(Passage(piece, page.title, page.page))
        self._build_index()

    def _build_index(self) -> None:
        if not self.passages:
            return
        self._vectorizer = TfidfVectorizer(
            stop_words="english",     # ignore "the", "and", ...
            max_features=MAX_FEATURES,
            ngram_range=(1, 2),       # also match two-word phrases
            sublinear_tf=True,        # dampen words repeated many times
        )
        self._matrix = self._vectorizer.fit_transform(p.text for p in self.passages)

    # ---------- searching ----------
    def search(self, query: str, top_k: int = TOP_K) -> List[Passage]:
        """Return the `top_k` most similar passages, best first."""
        if self._vectorizer is None or self._matrix is None:
            return []

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix).ravel()

        best_first = scores.argsort()[::-1][:top_k]
        return [
            replace(self.passages[i], score=float(scores[i]))
            for i in best_first
            if scores[i] > 0          # drop passages sharing no words
        ]

    # ---------- info for the UI ----------
    def stats(self) -> Dict[str, int]:
        return {
            "documents": len({p.title for p in self.passages}),
            "pages": len({(p.title, p.page) for p in self.passages}),
            "chunks": len(self.passages),
        }
