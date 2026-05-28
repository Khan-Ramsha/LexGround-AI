# LexGround-AI

LexGround-AI is a simple legal document drafting assistant.

You upload a legal file (PDF, image, or DOCX), and the app:
- reads the document,
- finds important facts,
- builds a draft "Case Fact Summary",
- and learns from your edits for future drafts.

This project is built with FastAPI and uses retrieval + LLM generation.

## What This Repo Contains

- `main.py` - FastAPI app and API endpoints.
- `document_processing.py` - file conversion, text chunking, and field extraction.
- `retrieval.py` - embeddings + FAISS vector search.
- `generator.py` - prompt creation and draft generation.
- `editor.py` - compares original vs edited draft and learns correction rules.
- `store_edits.py` - SQLite table setup (`edits`, `rules`).
- `tests/` - unit tests for generator and editor logic.
- `artifacts/` - uploaded files and generated sample files.

## Tech Stack

- Python
- FastAPI + Uvicorn
- Docling (document processing)
- SentenceTransformers + FAISS (semantic retrieval)
- Groq API (LLM draft generation)
- SQLite (stores edits/rules)
- Pytest (tests)

## Quick Start (Local)

### 1) Clone and enter project

```bash
git clone <your-repo-url>
cd LexGround-AI
```

### 2) Create virtual environment

Windows (PowerShell):

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Set environment variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_key_here
LOG_LEVEL=INFO
```

Notes:
- `GROQ_API_KEY` is needed for real LLM output.
- If key is missing, code may use fallback behavior.

### 5) Run server

```bash
uvicorn main:app --reload
```

Server runs at: `http://127.0.0.1:8000`

## Docker Run

```bash
docker build -t lexground-ai .
docker run -p 8000:8000 --env-file .env lexground-ai
```

## API Endpoints (Simple)

### Health check

`GET /health`

Response:

```json
{"status":"ok"}
```

### Upload and auto-generate draft

`POST /upload/` (multipart form-data with `file`)

Accepted extensions:
- `.pdf`
- `.png`
- `.jpeg`
- `.jpg`
- `.docx`

Response includes:
- `document_name`
- `draft`
- `evidence_used`
- `structured_fields`
- `few_shot_applied`

### Save user edits

`POST /edit/`

Request body:

```json
{
  "document_name": "stored_file_name_here",
  "edited_draft": "your corrected draft text"
}
```

This stores changes and a learned rule in SQLite for future prompts.

## Architecture 
<img width="672" height="863" alt="image" src="https://github.com/user-attachments/assets/5c3e0a5e-7bab-47e7-9762-41ef8aadbbb6" />

## Run Tests

```bash
pytest
```
