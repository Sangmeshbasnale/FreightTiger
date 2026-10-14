import re
from datetime import datetime
from pathlib import Path
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

MONTH_NAMES = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6,
    "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12
}

class PlainEnglishQAAssistant:
    def __init__(self, submission_csv: str = "outputs/submission.csv"):
        self.sub_path = Path(submission_csv)
        if not self.sub_path.exists():
            raise FileNotFoundError(f"Submission results not found at {submission_csv}. Run pipeline first.")
        self.df = pd.read_csv(self.sub_path)
        self.routes = self.df["route"].unique().tolist()

    def _extract_route(self, query: str) -> Optional[str]:
        q_lower = query.lower()
        for r in self.routes:
            parts = r.lower().split("-")
            if parts[0] in q_lower and parts[1] in q_lower:
                return r
        return None

    def _extract_date_or_month(self, query: str) -> Tuple[Optional[int], Optional[int]]:
        q_lower = query.lower()
        year_match = re.search(r"\b(202[45])\b", q_lower)
        year = int(year_match.group(1)) if year_match else None

        month = None
        for m_name, m_num in MONTH_NAMES.items():
            if re.search(rf"\b{m_name}\b", q_lower):
                month = m_num
                break

        return year, month

    def answer_query(self, query: str) -> str:
        """
        Answers plain-English questions regarding shipping costs, spikes, and justifications.
        """
        route = self._extract_route(query)
        year, month = self._extract_date_or_month(query)

        subset = self.df.copy()
        if route:
            subset = subset[subset["route"] == route]

        if year:
            subset = subset[subset["week_of"].str.startswith(str(year))]

        if month:
            subset = subset[subset["week_of"].apply(lambda d: int(d.split("-")[1]) == month)]

        if subset.empty:
            return f"I couldn't find any recorded data for query '{query}'. Please specify an active corridor (e.g., Ahmedabad-Mumbai, Delhi-Jaipur) and time period."

        # Filter for flagged or notable rows first
        anomalies = subset[subset["flagged"] != "No"]

        if not anomalies.empty:
            responses = []
            for _, row in anomalies.iterrows():
                r_name = row["route"]
                w_of = row["week_of"]
                cost = row["cost_per_tonne_km"]
                flag = row["flagged"]
                note = row["matched_note_id"] if pd.notna(row["matched_note_id"]) and row["matched_note_id"] else "None"
                reason = row["reason"]
                vs_own = row["vs_own_history"]
                vs_peer = row["vs_similar_routes"]

                if flag == "No (justified)":
                    resp = (
                        f"On route {r_name} during the week of {w_of}, cost rose to {cost:.2f} INR/tonne-km "
                        f"({vs_own}, {vs_peer}). This increase was JUSTIFIED by Note {note}: {reason}"
                    )
                else:
                    resp = (
                        f"On route {r_name} during the week of {w_of}, an unusual cost spike was detected "
                        f"at {cost:.2f} INR/tonne-km ({vs_own}, {vs_peer}). Flag: {flag}. Finding: {reason}"
                    )
                responses.append(resp)
            return "\n\n".join(responses)
        else:
            avg_cost = subset["cost_per_tonne_km"].mean()
            return (
                f"During this period on {route or 'the queried routes'}, shipping costs remained stable and normal "
                f"(average: {avg_cost:.2f} INR/tonne-km). No unusual spikes or cost anomalies were flagged."
            )
