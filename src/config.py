"""
config.py - one place for every path, default value and model name.

Why a config module?
    Before, numbers like 220 (chunk size) and file names were repeated in
    several files. Now you change them here and the whole project follows.
"""

from __future__ import annotations

import os
from pathlib import Path

# Optional: load secrets from a local ".env" file (never commit that file!).
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is nice to have, not required
    pass

# ---------- Paths ----------
# Path(__file__) is this file; .parent.parent walks up to the project root.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"              # source documents (the PDF)
HISTORY_DIR = DATA_DIR / "history"      # chat history (git-ignored)

DEFAULT_PDF = RAW_DIR / "research_and_knowledge_discovery.pdf"
HISTORY_FILE = HISTORY_DIR / "chat_history.json"

# ---------- Chunking / retrieval defaults ----------
CHUNK_SIZE = 220        # words per chunk
CHUNK_OVERLAP = 40      # words shared between neighbouring chunks
MIN_CHUNK_WORDS = 15    # tiny leftovers are not worth indexing
TOP_K = 4               # how many passages we retrieve per question
MAX_FEATURES = 20_000   # vocabulary size for TF-IDF

# ---------- Answer engines ----------
PROVIDERS = ("extractive", "gemini", "claude")

# Model names can be overridden from the environment / .env file,
# because providers retire old models from time to time.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
CLAUDE_MAX_TOKENS = 800

# Which environment variable holds the key for each provider.
API_KEY_ENV = {"gemini": "GEMINI_API_KEY", "claude": "ANTHROPIC_API_KEY"}


def get_api_key(provider: str, typed_key: str = "") -> str:
    """Return the key typed in the UI, or fall back to the environment."""
    return typed_key.strip() or os.getenv(API_KEY_ENV.get(provider, ""), "")
