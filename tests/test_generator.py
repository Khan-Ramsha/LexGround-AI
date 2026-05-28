from generator import generate_draft


def test_generate_draft_returns_fallback_when_no_key():
    chunks = [
        {
            "chunk_id": "doc_chunk_1",
            "chunk": "Agreement date is May 28, 2026. Liability cap is $5,000.",
            "metadata": {"source": "doc.pdf", "chunk_index": 1},
        }
    ]
    structured = {
        "dates": ["May 28, 2026"],
        "parties": [],
        "monetary_amounts": ["$5,000"],
    }

    output = generate_draft(chunks, structured)
    assert "Case Fact Summary" in output["draft"]
    assert "[E1]" in output["draft"]
    assert output["evidence_count"] == 1
