import pandas as pd
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

OUTPUT_COLUMNS = [
    "route",
    "week_of",
    "cost_per_tonne_km",
    "vs_own_history",
    "vs_similar_routes",
    "flagged",
    "matched_note_id",
    "reason"
]

def format_cost(val) -> str:
    if pd.isna(val):
        return ""
    # Standard 2 decimals using half-up rounding
    d = Decimal(str(val))
    return str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def write_submission_csv(
    df: pd.DataFrame,
    output_path: str = "outputs/submission.csv",
    mode: str = "all_route_weeks"
) -> Path:
    """
    Formats and writes the final submission CSV strictly adhering to the contract:
    route,week_of,cost_per_tonne_km,vs_own_history,vs_similar_routes,flagged,matched_note_id,reason
    """
    out_df = df.copy()

    # If anomalies_only mode, filter out flagged == 'No'
    if mode == "anomalies_only":
        out_df = out_df[out_df["flagged"] != "No"].copy()

    # Ensure deterministic sorting
    out_df = out_df.sort_values(["route", "week_of"]).reset_index(drop=True)

    # Format fields
    out_df["cost_per_tonne_km"] = out_df["cost_per_tonne_km"].apply(format_cost)
    out_df["matched_note_id"] = out_df["matched_note_id"].fillna("").astype(str).str.strip()
    out_df["vs_own_history"] = out_df["vs_own_history"].fillna("").astype(str)
    out_df["vs_similar_routes"] = out_df["vs_similar_routes"].fillna("").astype(str)
    out_df["flagged"] = out_df["flagged"].fillna("No").astype(str)
    out_df["reason"] = out_df["reason"].fillna("").astype(str)

    # Validate all columns present
    for col in OUTPUT_COLUMNS:
        if col not in out_df.columns:
            raise KeyError(f"Missing required output column: {col}")

    # Retain strictly the required columns in exact order
    final_csv_df = out_df[OUTPUT_COLUMNS]

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    final_csv_df.to_csv(out_file, index=False, encoding="utf-8")
    return out_file
