"""
Run with:  python -m pytest
Small tests that protect the core logic from silent breakage.
"""

import tempfile
from pathlib import Path

from src.chunking import clean_text, split_into_chunks
from src.history import load_history, make_entry, save_history
from src.knowledge_base import KnowledgeBase
from src.pdf_loader import PageText
from src.rag_pipeline import answer_question

CATS = ("Cats are small carnivorous mammals that purr, hunt mice at night and sleep "
        "for most of the day while grooming their soft fur very carefully every hour.")
ROCKETS = ("Rockets burn fuel to produce thrust, lifting satellites into orbit where "
           "they circle the planet and relay signals for navigation and weather forecasts.")


def make_kb() -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.add_pages([PageText(CATS, "doc.pdf", 1), PageText(ROCKETS, "doc.pdf", 2)],
                 chunk_size=40, overlap=5)
    return kb


# ---------- chunking ----------
def test_clean_text_removes_wiki_headings():
    assert clean_text("Intro text\n== See also ==\nMore text") == "Intro text More text"


def test_chunks_overlap_and_cover_text():
    text = " ".join(f"w{i}" for i in range(100))
    chunks = split_into_chunks(text, chunk_size=40, overlap=10, min_words=5)
    assert chunks[0].split()[-10:] == chunks[1].split()[:10]   # shared words
    assert "w99" in chunks[-1]                                 # nothing lost at the end


def test_bad_overlap_raises():
    try:
        split_into_chunks("a b c", chunk_size=10, overlap=10)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


# ---------- retrieval ----------
def test_search_finds_the_right_page():
    hits = make_kb().search("how do rockets reach orbit?", top_k=2)
    assert hits and hits[0].page == 2


def test_search_with_no_overlap_returns_nothing():
    assert make_kb().search("zzzz qqqq") == []


# ---------- pipeline & history ----------
def test_pipeline_extractive_and_fallback_without_key():
    kb = make_kb()
    result = answer_question("what do cats do?", kb, provider="claude", api_key="")
    assert result.provider_used == "extractive" and result.sources


def test_history_roundtrip():
    kb = make_kb()
    result = answer_question("cats", kb)
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "h.json"
        save_history([make_entry("cats", result, "extractive")], path)
        assert load_history(path)[0]["question"] == "cats"
        path.write_text("{ broken json", encoding="utf-8")
        assert load_history(path) == []     # corrupt file doesn't crash the app
