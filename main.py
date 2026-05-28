from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
from pathlib import Path
import logging
from document_processing import DocumentProcessor
from retrieval import DocumentIndex
from generator import generate_draft
from editor import save_edit, get_few_shot_examples
from store_edits import init_db
import uuid
import shutil
from app_logging import setup_logging

app = FastAPI()
setup_logging()
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("artifacts")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpeg", ".jpg", ".docx"}

_docs = {}
_indexes = {}
_drafts = {}

SECTION_QUERIES = {
    "parties": "plaintiff defendant petitioner respondent parties involved",
    "case_background": "nature of dispute agreement complaint conflict background",
    "timeline": "dates events timeline notice communication meeting payment",
    "claims": "allegation breach violation negligence fraud non-payment",
    "financials": "rent payment deposit compensation invoice amount",
    "evidence": "email receipt attachment annexure signed copy proof",
    "termination": "termination cancellation notice breach agreement end"
}

@app.on_event("startup")
def startup():
    init_db()
    logger.info("Application startup complete")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload/")
async def upload(file: UploadFile):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Unsupported file type")

    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        logger.info("Upload received: filename=%s", file.filename)
        processor = DocumentProcessor()
        result = processor.process_file(str(file_path))
        if not isinstance(result, dict) or "chunks" not in result:
            raise ValueError("Invalid processing result format.")
        if not result["chunks"]:
            raise ValueError("No usable text chunks extracted from document.")

        idx = DocumentIndex()
        idx.build(result["chunks"])

        _docs[filename] = result
        _indexes[filename] = idx
        logger.info("Document processed: stored_name=%s chunks=%s", filename, len(result["chunks"]))

        # generate draft immediately
        retrieved_sections = {
            section: idx.search(query, top_k=3)
            for section, query in SECTION_QUERIES.items()
        }
        few_shot = get_few_shot_examples(limit=3)
        output = generate_draft(retrieved_sections, result["structured"], few_shot)
        _drafts[filename] = output["draft"]

    except Exception as e:
        logger.exception("Processing failed for filename=%s", file.filename)
        raise HTTPException(500, f"Processing failed: {str(e)}")

    return {
        "document_name": filename,
        "draft": output["draft"],
        "evidence_used": output["evidence_used"],
        "structured_fields": result["structured"],
        "few_shot_applied": bool(few_shot),
    }

class EditRequest(BaseModel):
    document_name: str
    edited_draft: str

@app.post("/edit/")
def edit(req: EditRequest):
    if req.document_name not in _drafts:
        raise HTTPException(404, "No draft found. Upload document first.")

    original = _drafts[req.document_name]
    result = save_edit(req.document_name, original, req.edited_draft)
    logger.info("Edit captured: document=%s", req.document_name)

    return {
        "message": "Edit saved. Future drafts will improve.",
        "learned_rule": result["learned_rule"],
        "changes_captured": result["actual_changes"],
    }