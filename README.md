# 🔭 ResearchLens - RAG over "Research & Knowledge Discovery"

A small Retrieval-Augmented Generation (RAG) app. It reads a PDF compiled from
Wikipedia and arXiv, finds the passages most relevant to your question using
TF-IDF, and answers either with plain extracted passages or with Gemini / Claude.

## How it works

```
question ──► TF-IDF search ──► top-K passages ──► answer engine ──► answer + sources
              (knowledge_base)                    (generators)
```

1. `pdf_loader` extracts the text of each page.
2. `chunking` cleans it and splits it into overlapping word windows.
3. `knowledge_base` indexes the chunks with TF-IDF and ranks them by cosine similarity.
4. `rag_pipeline` calls the chosen engine (extractive, Gemini, or Claude).
5. `app.py` shows the chat, the sources with relevance bars, and simple analytics.

## Project structure

```
research-knowledge-discovery/
├── app.py                  # Streamlit UI (entry point)
├── src/
│   ├── config.py           # paths, defaults, model names
│   ├── data_builder.py     # builds the PDF from Wikipedia + arXiv
│   ├── pdf_loader.py       # PDF -> page text
│   ├── chunking.py         # text cleaning + chunking
│   ├── knowledge_base.py   # TF-IDF index + search
│   ├── generators.py       # extractive / Gemini / Claude answers
│   ├── rag_pipeline.py     # question -> answer
│   ├── history.py          # chat history (JSON)
│   └── ui_styles.py        # CSS
├── data/
│   ├── raw/                # source PDF
│   └── history/            # your chats (git-ignored)
├── tests/test_rag.py
├── requirements.txt        # run the app
├── requirements-build.txt  # rebuild the PDF
├── requirements-dev.txt    # tests
└── .env.example
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
```

API keys are optional. The extractive engine works without any. To use Gemini
or Claude, copy `.env.example` to `.env` and add a key, or paste it in the sidebar.

## Run

```bash
streamlit run app.py
```

### Rebuild the PDF (optional, needs internet)

```bash
pip install -r requirements-build.txt
python -m src.data_builder --results 2
```

### Run the tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Ideas for next steps

- Replace TF-IDF with sentence embeddings (e.g. `sentence-transformers`) and compare results.
- Let users upload their own PDF.
- Add an evaluation set of questions with expected pages.
