from typing import Dict, Any, Optional

def render_justified_reason(note: Dict[str, Any]) -> str:
    """
    Renders the plain-English explanation for a validated justifying note.
    Format: Matches note {note_id} dated {date}: {reason_summary}. The cost rise has a clear explanation.
    """
    return f"Matches note {note['note_id']} dated {note['date']}: {note['reason_summary']}. The cost rise has a clear explanation."

def render_unexplained_with_nearby_note(closest_note: Dict[str, Any]) -> str:
    """
    Renders explanation when an anomaly has a nearby non-qualifying note.
    Format: The closest note ({note_id}, {date}) mentions {reason_summary} -- it does not describe a reason for a cost rise on this route. No genuine justification found; flagged for review.
    """
    return (
        f"The closest note ({closest_note['note_id']}, {closest_note['date']}) "
        f"mentions {closest_note['reason_summary']} -- it does not describe a reason for a cost rise on this route. "
        f"No genuine justification found; flagged for review."
    )

def render_unexplained_default() -> str:
    """
    Renders explanation when no matching or nearby note exists.
    Format: No matching note found for this route or date range. Cost rise looks unexplained and worth a human review.
    """
    return "No matching note found for this route or date range. Cost rise looks unexplained and worth a human review."

def render_normal_reason() -> str:
    """
    Renders explanation for normal non-anomalous route-weeks.
    """
    return "No unusual cost rise detected relative to this route's history or similar routes."
