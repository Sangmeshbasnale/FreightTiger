from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

# Explicit curated rules per user requirements and plan.md
CURATED_NOTE_METADATA = {
    "N001": {
        "can_justify": True,
        "effective_start": "2025-02-24",
        "effective_end": "2025-03-08",
        "effect": "cost_increase",
        "reason_summary": "heavy flooding on the Chennai-Bangalore highway forced longer detours and higher trip costs"
    },
    "N002": {
        "can_justify": True,
        "effective_start": "2025-01-20",
        "effective_end": "2025-01-26",
        "effect": "cost_increase",
        "reason_summary": "a regional festival week drove a temporary surcharge on this corridor"
    },
    "N003": {
        "can_justify": True,
        "effective_start": "2025-05-05",
        "effective_end": "2025-06-01",
        "effect": "cost_increase",
        "reason_summary": "diesel prices rose nationwide, pushing up transportation costs across all routes by roughly 5-7%"
    },
    "N004": {
        "can_justify": False,
        "effective_start": "2024-03-11",
        "effective_end": "2024-03-17",
        "effect": "unrelated",
        "reason_summary": "toll plaza commissioned on routes not part of this dataset"
    },
    "N005": {
        "can_justify": False,
        "effective_start": "2024-07-29",
        "effective_end": "2024-08-04",
        "effect": "none",
        "reason_summary": "highway maintenance caused minor delays but costs were not significantly affected"
    },
    "N006": {
        "can_justify": False,
        "effective_start": "2025-09-22",
        "effective_end": "2025-09-28",
        "effect": "stable",
        "reason_summary": "stable demand with no major disruptions"
    },
    "N007": {
        "can_justify": False,
        "effective_start": "2024-05-20",
        "effective_end": "2024-05-26",
        "effect": "improved_road",
        "reason_summary": "improved road conditions after resurfacing work"
    },
    "N008": {
        "can_justify": False,
        "effective_start": "2025-06-09",
        "effective_end": "2025-06-15",
        "effect": "stable",
        "reason_summary": "no significant disruptions reported; freight movement normal"
    },
    "N009": {
        "can_justify": False,
        "effective_start": "2025-03-17",
        "effective_end": "2025-03-23",
        "effect": "normalization",
        "reason_summary": "route returned to normal conditions after flood repairs completed"
    },
    "N010": {
        "can_justify": False,
        "effective_start": "2025-10-27",
        "effective_end": "2025-11-02",
        "effect": "absorbed_cost",
        "reason_summary": "compliance costs for vehicle tracking were absorbed without rate change"
    }
}

class NotesRegistry:
    def __init__(self, notes_df: pd.DataFrame):
        self.notes: Dict[str, Dict[str, Any]] = {}
        for _, row in notes_df.iterrows():
            n_id = str(row["note_id"]).strip()
            meta = CURATED_NOTE_METADATA.get(n_id, {
                "can_justify": False,
                "effective_start": str(row["date"]),
                "effective_end": str(row["date"]),
                "effect": "unknown",
                "reason_summary": str(row["note"])
            })
            self.notes[n_id] = {
                "note_id": n_id,
                "date": str(row["date"]).strip(),
                "applies_to": str(row["applies_to"]).strip(),
                "note": str(row["note"]).strip(),
                "can_justify": meta["can_justify"],
                "effective_start": meta["effective_start"],
                "effective_end": meta["effective_end"],
                "effect": meta["effect"],
                "reason_summary": meta["reason_summary"]
            }

    def get_all_notes(self) -> List[Dict[str, Any]]:
        return list(self.notes.values())

    def get_note(self, note_id: str) -> Dict[str, Any]:
        return self.notes.get(note_id)
