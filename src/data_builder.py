"""
data_builder.py - build the knowledge PDF from Wikipedia + arXiv.

Run it once (needs internet) from the project root:

    python -m src.data_builder
    python -m src.data_builder --results 3 --output data/raw/my_topic.pdf

The generated PDF is what the RAG app reads.
"""

from __future__ import annotations

import argparse
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List
from xml.sax.saxutils import escape  # makes text safe for reportlab's mini-HTML

from .config import DEFAULT_PDF

logger = logging.getLogger(__name__)

# Every subtopic gets its own fetch pass, which keeps coverage broad.
SUBTOPICS = [
    "Research",
    "Scientific method",
    "Research methodology",
    "Knowledge discovery",
    "Knowledge discovery in databases",
    "Data mining",
    "Information retrieval",
    "Literature review",
    "Systematic review",
    "Knowledge management",
    "Research question",
    "Qualitative research",
    "Quantitative research",
    "Peer review",
]

_WIKI_HEADING = re.compile(r"^=+\s*(.*?)\s*=+$")  # "== History ==" -> "History"


@dataclass
class Section:
    """One fetched article or paper."""
    source: str   # "Wikipedia" or "arXiv"
    title: str
    text: str


# ---------- Fetching ----------
def fetch_wikipedia(topic: str, max_results: int) -> List[Section]:
    import wikipedia  # imported here: only needed when building the PDF

    sections: List[Section] = []
    try:
        for title in wikipedia.search(topic, results=max_results):
            try:
                page = wikipedia.page(title, auto_suggest=False)
                sections.append(Section("Wikipedia", page.title, page.content))
            except (wikipedia.DisambiguationError, wikipedia.PageError):
                continue  # ambiguous / missing page: skip it
    except Exception as exc:
        logger.warning("Wikipedia error for %r: %s", topic, exc)
    return sections


def fetch_arxiv(topic: str, max_results: int) -> List[Section]:
    import arxiv

    sections: List[Section] = []
    try:
        search = arxiv.Search(
            query=topic, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance
        )
        for paper in arxiv.Client().results(search):
            sections.append(Section("arXiv", paper.title, paper.summary))
    except Exception as exc:
        logger.warning("arXiv error for %r: %s", topic, exc)
    return sections


# ---------- PDF building ----------
def build_pdf(output_path: Path, subtopics: List[str], results_per_subtopic: int) -> int:
    """Fetch every subtopic and write the PDF. Returns the number of sections."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleBig", parent=styles["Title"], fontSize=24, spaceAfter=10)
    subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"],
                                    textColor=colors.HexColor("#555555"), spaceAfter=20)
    topic_style = ParagraphStyle("Topic", parent=styles["Heading1"], spaceBefore=10, spaceAfter=4)
    article_style = ParagraphStyle("Article", parent=styles["Heading2"], spaceBefore=14, spaceAfter=8)
    meta_style = ParagraphStyle("Meta", parent=styles["Normal"],
                                textColor=colors.HexColor("#666666"), spaceAfter=10)

    story = [
        Paragraph("Research and Knowledge Discovery", title_style),
        Paragraph("A compiled reference covering research methodology, the scientific "
                  "process, knowledge discovery, data mining, and information retrieval, "
                  "sourced from Wikipedia and arXiv.", subtitle_style),
        Spacer(1, 12),
        PageBreak(),
    ]

    total = 0
    for topic in subtopics:
        logger.info("Fetching: %s ...", topic)
        sections = fetch_wikipedia(topic, results_per_subtopic) + fetch_arxiv(topic, results_per_subtopic)
        if not sections:
            continue

        story.append(Paragraph(escape(topic), topic_style))
        for section in sections:
            story.append(Paragraph(escape(section.title), article_style))
            story.append(Paragraph(f"Source: {section.source}", meta_style))
            for line in section.text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                heading = _WIKI_HEADING.match(line)
                if heading:   # show "== History ==" as a real bold heading
                    story.append(Paragraph(f"<b>{escape(heading.group(1))}</b>", styles["Normal"]))
                else:
                    story.append(Paragraph(escape(line), styles["Normal"]))
                story.append(Spacer(1, 6))
            total += 1
        story.append(PageBreak())

    if total == 0:
        raise RuntimeError("Nothing was fetched. Check your internet connection.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(output_path), pagesize=letter,
                      topMargin=0.8 * inch, bottomMargin=0.8 * inch).build(story)
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the knowledge PDF.")
    parser.add_argument("--output", type=Path, default=DEFAULT_PDF, help="PDF path to write")
    parser.add_argument("--results", type=int, default=2, help="articles/papers per subtopic")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    total = build_pdf(args.output, SUBTOPICS, args.results)
    print(f"PDF created: {args.output} ({total} sections across {len(SUBTOPICS)} subtopics)")


if __name__ == "__main__":
    main()
