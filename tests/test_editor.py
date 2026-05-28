from editor import classify_change, extract_changes


def test_classify_change_handles_unbalanced_lines():
    removed = ["**Parties:** Not found in document"]
    added = [
        "**Parties:** Apex Global Technologies, Independent Operator",
        "**Key Dates:** May 28, 2026",
    ]
    result = classify_change(removed, added)
    assert "FIELD FILLED" in result or "LINE REPLACED" in result


def test_extract_changes_has_added_and_removed_sections():
    original = "**Parties:** Not found in document\n"
    edited = "**Parties:** Apex Global Technologies\n"
    summary, removed, added = extract_changes(original, edited)
    assert "REMOVED:" in summary
    assert "ADDED:" in summary
    assert len(removed) == 1
    assert len(added) == 1