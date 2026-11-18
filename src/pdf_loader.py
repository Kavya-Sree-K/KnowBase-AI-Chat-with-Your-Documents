"""
pdf_loader.py - read a PDF and return the text of each page.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Union

from pypdf import PdfReader


@dataclass(frozen=True)
class PageText:
    """The raw text of one PDF page (before chunking)."""
    text: str
    title: str   # file name, shown as the citation
    page: int    # 1-based page number


def load_pdf(source: Union[str, Path]) -> List[PageText]:
    """
    Extract text from every non-empty page.

    `source` is a path. (A file-like object such as a Streamlit upload also
    works because pypdf accepts both.)
    """
    if isinstance(source, (str, Path)) and not Path(source).exists():
        raise FileNotFoundError(f"PDF not found: {source}")

    reader = PdfReader(source)
    title = Path(getattr(source, "name", str(source))).name

    pages: List[PageText] = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""   # scanned pages return None/""
        if text.strip():
            pages.append(PageText(text=text, title=title, page=number))
    return pages
