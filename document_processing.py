import os
import re
from typing import Any, Dict, List
import logging

from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Docling handles OCR for scanned/image-like pages internally.
        self.converter = DocumentConverter()

    def _extract_fields(self, full_text: str) -> Dict[str, List[Any]]:
        """Pull structured legal fields using regex heuristics."""
        return {
            "dates": list(
                set(
                    re.findall(
                        r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\w+ \d{1,2},? \d{4})\b",
                        full_text,
                    )
                )
            ),
            "parties": list(
                set(
                    re.findall(
                        r'(?:Licensor|Licensee|Plaintiff|Defendant|Petitioner|Respondent|Discloser|Recipient|Contractor)[:\s]+([A-Z][^\n,;]{3,70})',
                        full_text,
                        re.IGNORECASE,
                    )
                )
            ),
            "monetary_amounts": list(
                set(
                    re.findall(
                        r"(?:Rs\.?|INR|₹)\s?[\d,]+(?:\.\d{2})?|\$[\d,]+(?:\.\d{2})?",
                        full_text,
                    )
                )
            ),
            "case_numbers": list(
                set(
                    re.findall(
                        r"(?:Case|No\.|Docket|Agreement\s*No|Reference)[.:\s#-]*([A-Z0-9\-/]+)",
                        full_text,
                        re.IGNORECASE,
                    )
                )
            ),
            "durations": list(
                set(re.findall(r"\b(\d+)\s*(month|year|day)s?\b", full_text, re.IGNORECASE))
            ),
            "addresses": list(
                set(
                    re.findall(
                        r"\d+[,\s]+(?:[A-Z][a-z]+\s){1,6}(?:Street|Road|Avenue|Nagar|Colony|Marg|Lane)\b",
                        full_text,
                    )
                )
            ),
        }

    def _chunk_markdown(self, markdown_content: str) -> List[str]:
        raw_chunks = [chunk.strip() for chunk in markdown_content.split("\n\n") if chunk.strip()]
        # Drop trivial noise chunks while preserving legal clauses.
        return [chunk for chunk in raw_chunks if len(chunk) >= 25]

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Convert messy documents into chunked text + structured fields."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        source_name = os.path.basename(file_path)
        logger.info("Starting document processing: source=%s", source_name)
        result = self.converter.convert(file_path)
        markdown_content = result.document.export_to_markdown()
        chunks = self._chunk_markdown(markdown_content)

        structured_chunks = []
        for idx, chunk in enumerate(chunks):
            structured_chunks.append(
                {
                    "id": f"{source_name}_chunk_{idx}",
                    "text": chunk,
                    "metadata": {
                        "source": source_name,
                        "chunk_index": idx,
                    },
                }
            )

        full_text = "\n\n".join(chunk["text"] for chunk in structured_chunks)
        fields = self._extract_fields(full_text)

        output = {
            "source": source_name,
            "full_text": full_text,
            "chunks": structured_chunks,
            "structured": fields,
        }
        logger.info(
            "Document processing complete: source=%s chunks=%s fields=%s",
            source_name,
            len(structured_chunks),
            [k for k, v in fields.items() if v],
        )
        return output