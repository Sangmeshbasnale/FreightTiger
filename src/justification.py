import pandas as pd
from datetime import timedelta
from typing import Dict, Any, Optional, Tuple
from src.retrieval import NoteRetriever
from src.explanation import (
    render_justified_reason,
    render_unexplained_with_nearby_note,
    render_unexplained_default
)

ALLOWED_JUSTIFYING_NOTES = {"N001", "N002", "N003"}
PROXIMITY_DAYS_WINDOW = 21  # Within 3 weeks to be considered "closest note"

def check_overlap(week_of_str: str, note_start_str: str, note_end_str: str) -> bool:
    """
    Checks if week (Monday to Sunday) overlaps [note_start, note_end].
    Formula: week_start <= note_end and week_end >= note_start
    """
    week_start = pd.to_datetime(week_of_str).date()
    week_end = week_start + timedelta(days=6)
    note_start = pd.to_datetime(note_start_str).date()
    note_end = pd.to_datetime(note_end_str).date()
    return (week_start <= note_end) and (week_end >= note_start)

def route_matches(route: str, applies_to: str) -> bool:
    applies = applies_to.strip().lower()
    return applies == "all routes" or applies == route.strip().lower()

def evaluate_justification(
    row: pd.Series,
    retriever: NoteRetriever
) -> Tuple[str, str, str]:
    """
    Evaluates an anomaly row against retrieved context notes.
    Returns:
    (flagged, matched_note_id, reason)
    """
    route = str(row["route"]).strip()
    week_of = str(row["week_of"]).strip()

    query = f"Freight cost increase on route {route} during week {week_of}. Cause of higher cost."
    retrieved = retriever.retrieve(query, top_k=5)

    # 1. Search for genuine justification
    valid_matches = []
    for note, score in retrieved:
        n_id = note["note_id"]
        if n_id in ALLOWED_JUSTIFYING_NOTES and note["can_justify"]:
            if route_matches(route, note["applies_to"]):
                if check_overlap(week_of, note["effective_start"], note["effective_end"]):
                    is_exact_route = (note["applies_to"].strip().lower() == route.lower())
                    valid_matches.append((is_exact_route, score, note))

    if valid_matches:
        valid_matches.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best_note = valid_matches[0][2]
        flagged = "No (justified)"
        matched_note_id = best_note["note_id"]
        reason = render_justified_reason(best_note)
        return flagged, matched_note_id, reason

    # 2. Not justified -> flagged = "Yes", matched_note_id = ""
    flagged = "Yes"
    matched_note_id = ""

    # Check for closest non-qualifying note
    week_date = pd.to_datetime(week_of).date()
    closest_note = None
    min_dist = float("inf")

    for note, _ in retrieved:
        if route_matches(route, note["applies_to"]):
            n_date = pd.to_datetime(note["date"]).date()
            dist = abs((week_date - n_date).days)
            if dist <= PROXIMITY_DAYS_WINDOW and dist < min_dist:
                min_dist = dist
                closest_note = note

    if closest_note is not None:
        reason = render_unexplained_with_nearby_note(closest_note)
    else:
        reason = render_unexplained_default()

    return flagged, matched_note_id, reason
