import difflib
import os
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
import sqlite3
import logging

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None
logger = logging.getLogger(__name__)

DB_PATH = "data/edits.db"


def extract_changes(original: str, edited: str) -> str:
    orig_lines = original.splitlines(keepends=True)
    edit_lines = edited.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        orig_lines, edit_lines,
        fromfile="original", tofile="edited", lineterm=""
    ))

    removed = [l[1:].strip() for l in diff if l.startswith("-") and not l.startswith("---")]
    added   = [l[1:].strip() for l in diff if l.startswith("+") and not l.startswith("+++")]
    summary = f"REMOVED:\n" + "\n".join(removed) + f"\n\nADDED:\n" + "\n".join(added)

    return summary, removed, added


def llm_extract_rule(actual_changes: str, change_classification: str) -> str:
    if client is None:
        logger.warning("GROQ_API_KEY not set; using fallback rule extraction")
        return "When key fields are missing, explicitly search retrieved evidence for parties, dates, obligations, and financial amounts before writing placeholders."

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=100,  
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": """You are a strict rule extractor for a legal AI system.
                Your ONLY job: given a before/after edit, write ONE short imperative instruction 
                that will prevent the same mistake in future drafts.

                Output format — a single sentence starting with an action verb:
                - "Always extract the termination clause date from Section X..."
                - "When rent amount is missing, search for currency symbols..."
                - "Format party names as FULL LEGAL NAME (role) on first mention..."

                Output the instruction only. No explanation. No preamble. No bullet point. One line."""
            },
            {
                "role": "user",
                "content": f"""The operator made this edit to a legal draft:
                WHAT CHANGED (classified):
                {change_classification}

                RAW DIFF:
                {actual_changes}

                Write the single corrective instruction now:"""
            }
        ]
    )
    return response.choices[0].message.content.strip()


def save_edit(document_name: str, original: str, edited: str) -> dict:
    actual_changes, removed, added = extract_changes(original, edited)
    classification = classify_change(removed, added)               
    learned_rule = llm_extract_rule(actual_changes, classification)
    conn = sqlite3.connect(DB_PATH)

    # Step 3: save the edit
    cursor = conn.execute("""
        INSERT INTO edits (document_name, original_draft, edited_draft, actual_changes, learned_pattern, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (document_name, original, edited, actual_changes, learned_rule, datetime.utcnow().isoformat()))

    edit_id = cursor.lastrowid

    # Step 4: save rule separately so it accumulates over time
    conn.execute("""
        INSERT INTO rules (rule, source_edit_id, timestamp)
        VALUES (?, ?, ?)
    """, (learned_rule, edit_id, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()
    logger.info("Stored edit and learned rule: document=%s", document_name)

    return {"actual_changes": actual_changes, "learned_rule": learned_rule}


def get_few_shot_examples(limit: int = 3) -> str:
    """Fetch accumulated rules — these go into next generation prompt."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT r.rule, e.original_draft, e.edited_draft
        FROM rules r
        JOIN edits e ON r.source_edit_id = e.id
        ORDER BY r.id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    if not rows:
        return ""

    examples = []
    for i, (rule, orig, edited) in enumerate(rows):
        examples.append(f"""
            Rule {i+1}: {rule}
            ORIGINAL (excerpt): {orig[:150]}
            REVISED TO: {edited[:150]}
        """)
    return "\n".join(examples)


def get_recent_rules(limit: int = 10) -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT rule FROM rules ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [row[0] for row in rows]


def classify_change(removed: list, added: list) -> str:
    """
    Figures out WHAT KIND of edit happened.
    This gives LLM better context to write a specific rule.
    """
    change_types = []

    # zip_longest-like behavior using max length to avoid dropping unpaired edits
    max_len = max(len(removed), len(added))
    for i in range(max_len):
        r = removed[i] if i < len(removed) else ""
        a = added[i] if i < len(added) else ""
        # same field, value changed
        if ":" in r and ":" in a:
            field_r = r.split(":")[0].strip()
            field_a = a.split(":")[0].strip()
            
            if field_r == field_a:  # same field name, value replaced
                old_val = r.split(":", 1)[1].strip()
                new_val = a.split(":", 1)[1].strip()
                change_types.append(
                    f"FIELD FILLED: '{field_r}' was '{old_val}' → operator changed to '{new_val}'"
                )
            else:
                change_types.append(f"LINE REPLACED: '{r.strip()}' → '{a.strip()}'")
        else:
            change_types.append(f"LINE REPLACED: '{r.strip()}' → '{a.strip()}'")

    return "\n".join(change_types) if change_types else "No material changes detected."