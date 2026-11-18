"""
history.py - save and load the chat history as a JSON file.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List

from .config import HISTORY_FILE
from .rag_pipeline import RagResult

logger = logging.getLogger(__name__)
Entry = Dict  # {"id", "question", "answer", "sources", "provider"}


def load_history(path: Path = HISTORY_FILE) -> List[Entry]:
    """Return saved chats, or [] if the file is missing or damaged."""
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("History file is corrupted, starting fresh: %s", path)
        return []


def save_history(history: List[Entry], path: Path = HISTORY_FILE) -> None:
    """Write to a temp file first, then swap, so a crash can't corrupt it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def make_entry(question: str, result: RagResult, provider: str) -> Entry:
    return {
        "id": uuid.uuid4().hex,
        "question": question,
        "answer": result.answer,
        "sources": [asdict(p) for p in result.sources],
        "provider": result.provider_used or provider,
    }


def export_markdown(history: List[Entry]) -> str:
    return "\n\n".join(f"### Q: {h['question']}\n{h['answer']}" for h in history)
