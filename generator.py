import os
from groq import Groq
from typing import List
from dotenv import load_dotenv
import logging

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a legal document analyst writing Case Fact Summaries.
RULES:
- Base EVERY statement on the provided evidence passages only
- If information is missing, write "Not found in document" — never guess
- Be concise and structured
- Never invent names, dates, or amounts
- Do not combine unrelated evidence passages
- If OCR text appears incomplete, mention uncertainty
- If evidence conflicts, explicitly mention the conflict
- Never infer missing facts
- Every factual claim must cite supporting evidence
- Do not hallucinate information
Use evidence references inline like [E1], [E2] in every section where claims are made.
Use all the above rules while generating output.

"""

def format_sectioned_evidence(retrieved_sections: dict) -> str:
    blocks = []

    evidence_counter = 1

    for section, chunks in retrieved_sections.items():

        blocks.append(f"\nSECTION: {section.upper()}\n")

        for chunk in chunks:

            blocks.append(
                f"[E{evidence_counter}] "
                f"(page={chunk.get('page', 'unknown')}, "
                f"chunk={chunk.get('chunk_id', 'unknown')}):\n"
                f"{chunk['chunk']}\n"
            )

            evidence_counter += 1

    return "\n".join(blocks)


def format_fields(structured: dict) -> str:
    lines = []
    for key, val in structured.items():
        if not val:
            continue
        if isinstance(val, list):
            def _stringify(item):
                if isinstance(item, tuple):
                    return " ".join(str(x) for x in item)
                return str(item)

            joined = ", ".join(_stringify(item) for item in val)
            lines.append(f"- {key}: {joined}")
        else:
            lines.append(f"- {key}: {val}")
    return "\n".join(lines) if lines else "No structured fields extracted."


def build_prompt(retrieved_sections: dict, structured: dict, few_shot: str = "") -> str:
    few_shot_block = f"""OPERATOR PREFERENCES (learn from these past edits):
{few_shot}
---
""" if few_shot else ""
    return f"""{few_shot_block}
EXTRACTED FIELDS:
{format_fields(structured)}

EVIDENCE PASSAGES FROM DOCUMENT:
{format_sectioned_evidence(retrieved_sections)}
---
{"APPLY THE OPERATOR PREFERENCES ABOVE BEFORE WRITING." if few_shot else ""}

Write a Case Fact Summary using ONLY the above. Use this exact structure and attach [E#] citations:

## Case Fact Summary

**Parties:** [Licensor and Licensee names if found]
**Document Type:** [type of agreement]
**Key Dates:** [all dates found]
**Key Terms:** [bullet list of important clauses]
**Financial Terms:** [rent, deposit, amounts]
**Obligations:** [what each party must do]
**Termination Conditions:** [how agreement ends]
**Evidence Gaps:** [what's blank or unclear in the document]
"""

def _fallback_grounded_draft(chunks: List[dict], structured: dict) -> str:
    evidence_refs = ", ".join([f"[E{i+1}]" for i in range(len(chunks))]) or "No evidence retrieved."
    parties = ", ".join(structured.get("parties", [])) or "Not found in document"
    dates = ", ".join(structured.get("dates", [])) or "Not found in document"
    amounts = ", ".join(structured.get("monetary_amounts", [])) or "Not found in document"
    return f"""## Case Fact Summary
**Parties:** {parties} {evidence_refs}
**Document Type:** Not found in document
**Key Dates:** {dates} {evidence_refs}
**Key Terms:**
- Not found in document (manual review needed)
**Financial Terms:** {amounts} {evidence_refs}
**Obligations:** Not found in document
**Termination Conditions:** Not found in document
**Evidence Gaps:** Citation-ready output generated without LLM because GROQ_API_KEY is missing.
"""

def generate_draft(retrieved_sections: dict, structured: dict, few_shot: str = "") -> dict:
    # Support both formats: a dict mapping sections->chunks (from the API)
    # or a flat list of chunks (used by unit tests).
    if isinstance(retrieved_sections, dict):
        chunks = [
            chunk
            for section_chunks in retrieved_sections.values()
            for chunk in section_chunks
        ]
        sections_for_prompt = retrieved_sections
    else:
        # it's a list of chunk dicts
        chunks = list(retrieved_sections)
        sections_for_prompt = {"evidence": chunks}
    if not chunks:
        return {
            "draft": "## Case Fact Summary\n\nNo evidence retrieved from the document.",
            "evidence_used": [],
            "evidence_count": 0,
        }

    prompt = build_prompt(sections_for_prompt, structured, few_shot)

    if client is None:
        logger.warning("GROQ_API_KEY not set; using deterministic fallback draft")
        draft = _fallback_grounded_draft(chunks, structured)
    else:
        logger.info("Generating draft with LLM: evidence_chunks=%s", len(chunks))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        draft = response.choices[0].message.content
        logger.info("Draft generation complete")

    return {
        "draft": draft,
        "evidence_used": chunks,
        "evidence_count": len(chunks)
    }