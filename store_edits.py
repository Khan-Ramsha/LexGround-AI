import sqlite3, os

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/edits.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS edits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_name TEXT,
            original_draft TEXT,
            edited_draft TEXT,
            actual_changes TEXT,
            learned_pattern TEXT,
            timestamp TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule TEXT,
            source_edit_id INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()