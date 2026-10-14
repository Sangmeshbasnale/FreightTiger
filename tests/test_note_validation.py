import pytest
from src.justification import check_overlap, route_matches, ALLOWED_JUSTIFYING_NOTES
from src.notes_registry import CURATED_NOTE_METADATA

def test_allowed_justifying_notes_exact_whitelist():
    # Only N001, N002, N003 are allowed to justify
    assert ALLOWED_JUSTIFYING_NOTES == {"N001", "N002", "N003"}
    for note_id, meta in CURATED_NOTE_METADATA.items():
        if note_id in ["N001", "N002", "N003"]:
            assert meta["can_justify"] is True, f"{note_id} should be True"
        else:
            assert meta["can_justify"] is False, f"Trap note {note_id} should be False"

def test_date_overlap_formula():
    # Note effective: 2025-02-24 to 2025-03-08
    # Week 1: 2025-02-24 (Feb 24 - Mar 02) -> Overlaps
    assert check_overlap("2025-02-24", "2025-02-24", "2025-03-08") is True
    # Week 2: 2025-03-03 (Mar 03 - Mar 09) -> Overlaps
    assert check_overlap("2025-03-03", "2025-02-24", "2025-03-08") is True
    # Week 3: 2025-03-10 (Mar 10 - Mar 16) -> Does NOT overlap
    assert check_overlap("2025-03-10", "2025-02-24", "2025-03-08") is False
    # Preceding Week: 2025-02-17 (Feb 17 - Feb 23) -> Does NOT overlap
    assert check_overlap("2025-02-17", "2025-02-24", "2025-03-08") is False

def test_route_matches():
    assert route_matches("Chennai-Bangalore", "Chennai-Bangalore") is True
    assert route_matches("Delhi-Jaipur", "All Routes") is True
    assert route_matches("Mumbai-Delhi", "Ahmedabad-Mumbai") is False
