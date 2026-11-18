"""
app.py - Streamlit front end for ResearchLens.

Run from the project root:
    streamlit run app.py

This file only handles the UI. The real work lives in src/:
    pdf_loader -> chunking -> knowledge_base -> generators -> rag_pipeline
"""

import html
import re
import time
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List

import streamlit as st

from src import config
from src.history import export_markdown, load_history, make_entry, save_history
from src.knowledge_base import KnowledgeBase
from src.pdf_loader import load_pdf
from src.rag_pipeline import answer_question
from src.ui_styles import CUSTOM_CSS

# ---------- Page setup ----------
st.set_page_config(page_title="ResearchLens · RAG", page_icon="🔭",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------- Session state ----------
def init_state() -> None:
    """Streamlit re-runs this script on every click; session_state survives."""
    defaults = {"history": load_history(), "active_id": None}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------- Cached resources ----------
@st.cache_resource(show_spinner="Loading knowledge base...")
def get_knowledge_base(pdf_path: str, chunk_size: int) -> KnowledgeBase:
    """Build the index once per (pdf, chunk_size) instead of on every click."""
    kb = KnowledgeBase()
    kb.add_pages(load_pdf(pdf_path), chunk_size=chunk_size)
    return kb


# ---------- Small UI helpers ----------
def bubble_html(text: str, role: str) -> str:
    """
    Chat bubble as HTML. We escape the text first: answers come from a PDF
    or an LLM, so they must never be injected into the page as raw HTML.
    """
    safe = html.escape(text)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)  # keep **bold**
    safe = safe.replace("$", "&#36;").replace("\n", "<br>")  # "$" would trigger LaTeX
    return f'<div class="bubble-{role}">{safe}</div>'


def show_bubble(text: str, role: str) -> None:
    st.markdown(bubble_html(text, role), unsafe_allow_html=True)


def typewriter(placeholder, text: str, step: int = 6, delay: float = 0.004) -> None:
    """Cosmetic 'typing' effect: reveal the answer a few characters at a time."""
    for end in range(step, len(text), step):
        placeholder.markdown(bubble_html(text[:end] + "▌", "bot"), unsafe_allow_html=True)
        time.sleep(delay)
    placeholder.markdown(bubble_html(text, "bot"), unsafe_allow_html=True)


def render_sources(sources: List[Dict]) -> None:
    if not sources:
        return
    with st.expander(f"📎 {len(sources)} source passage(s)"):
        for s in sources:
            pct = int(s["score"] * 100)
            st.markdown(f"**{s['title']}** · page {s['page']}")
            st.markdown(f'<div class="score-bar-bg"><div class="score-bar-fill" '
                        f'style="width:{pct}%"></div></div>', unsafe_allow_html=True)
            st.caption(f"relevance {pct}%")
            st.write(s["text"][:300] + "...")
            st.markdown("---")


def render_entry(entry: Dict) -> None:
    show_bubble(entry["question"], "user")
    show_bubble(entry["answer"], "bot")
    render_sources(entry.get("sources", []))


# ---------- Sidebar ----------
def render_sidebar():
    """Draws the sidebar and returns the user's settings plus the KB."""
    with st.sidebar:
        st.markdown("### 🔭 ResearchLens")
        st.caption("RAG over Research & Knowledge Discovery")

        provider = st.radio(
            "Answer engine", config.PROVIDERS,
            format_func=lambda p: {"extractive": "🧩 Extractive (no key)",
                                   "gemini": "✨ Gemini", "claude": "🟣 Claude"}[p])
        typed_key = ""
        if provider != "extractive":
            typed_key = st.text_input(f"{provider.title()} API key", type="password",
                                      help="Or set it in a .env file (see .env.example).")
        api_key = config.get_api_key(provider, typed_key)

        st.divider()
        chunk_size = st.slider("Chunk size (words)", 100, 400, config.CHUNK_SIZE, 20)
        top_k = st.slider("Top-K passages", 2, 8, config.TOP_K)

        kb = None
        if Path(config.DEFAULT_PDF).exists():
            kb = get_knowledge_base(str(config.DEFAULT_PDF), chunk_size)
            st.success(f"✓ Loaded {config.DEFAULT_PDF.name}")
        else:
            st.error("PDF not found. Run `python -m src.data_builder` first.")

        stats = kb.stats() if kb else {"pages": 0, "chunks": 0}
        col1, col2 = st.columns(2)
        col1.metric("Pages", stats["pages"])
        col2.metric("Chunks", stats["chunks"])

        st.divider()
        render_history_controls()
    return provider, api_key, top_k, kb, stats


def render_history_controls() -> None:
    st.markdown("#### 🕘 History")
    if st.button("➕ New chat", use_container_width=True):
        st.session_state.active_id = None
        st.rerun()

    for item in reversed(st.session_state.history):
        label = item["question"][:42] + ("…" if len(item["question"]) > 42 else "")
        st.markdown('<div class="hist-btn">', unsafe_allow_html=True)
        if st.button(f"💬 {label}", key=f"h_{item['id']}", use_container_width=True):
            st.session_state.active_id = item["id"]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.history:
        if st.button("🗑️ Clear history", use_container_width=True):
            st.session_state.history = []
            st.session_state.active_id = None
            save_history([])
            st.rerun()
        st.download_button("⬇️ Export chat (.md)", export_markdown(st.session_state.history),
                           file_name="chat_export.md", use_container_width=True)


# ---------- Tabs ----------
def render_chat(provider: str, api_key: str, top_k: int, kb) -> None:
    if kb is None:
        st.info("👈 The PDF is missing, so there is nothing to chat with yet.")
        return

    # Viewing one old conversation from the sidebar.
    if st.session_state.active_id:
        entry = next((h for h in st.session_state.history
                      if h["id"] == st.session_state.active_id), None)
        if entry:
            render_entry(entry)
        if st.button("← Back to live chat"):
            st.session_state.active_id = None
            st.rerun()
        return

    # Live chat: show everything so far, then wait for a new question.
    for entry in st.session_state.history:
        render_entry(entry)

    query = st.chat_input("Ask something about research & knowledge discovery...")
    if not query:
        return

    show_bubble(query, "user")
    placeholder = st.empty()
    placeholder.markdown(bubble_html("🔍 retrieving & thinking...", "bot"), unsafe_allow_html=True)

    result = answer_question(query, kb, provider, api_key, top_k)
    typewriter(placeholder, result.answer)
    render_sources([asdict(p) for p in result.sources])

    st.session_state.history.append(make_entry(query, result, provider))
    save_history(st.session_state.history)


def render_analytics(stats: Dict[str, int]) -> None:
    st.markdown("#### Session analytics")
    history = st.session_state.history
    c1, c2, c3 = st.columns(3)
    c1.metric("Questions asked", len(history))
    c2.metric("Pages in KB", stats["pages"])
    c3.metric("Chunks in KB", stats["chunks"])

    if history:
        counts: Dict[str, int] = {}
        for h in history:
            provider = h.get("provider", "extractive")
            counts[provider] = counts.get(provider, 0) + 1
        st.bar_chart(counts)


# ---------- Main ----------
def main() -> None:
    init_state()
    provider, api_key, top_k, kb, stats = render_sidebar()

    st.markdown('<p class="gradient-title">ResearchLens</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Ask questions grounded in Research & Knowledge Discovery.</p>',
                unsafe_allow_html=True)

    tab_chat, tab_analytics = st.tabs(["💬 Chat", "📊 Analytics"])
    with tab_chat:
        render_chat(provider, api_key, top_k, kb)
    with tab_analytics:
        render_analytics(stats)


main()
