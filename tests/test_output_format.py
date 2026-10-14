import pytest
import pandas as pd
from src.output_writer import OUTPUT_COLUMNS

def test_columns_contract_matches_sample():
    sample_cols = pd.read_csv("sample_output_format_v2.csv", nrows=1).columns.tolist()
    assert OUTPUT_COLUMNS == sample_cols
    assert OUTPUT_COLUMNS == [
        "route",
        "week_of",
        "cost_per_tonne_km",
        "vs_own_history",
        "vs_similar_routes",
        "flagged",
        "matched_note_id",
        "reason"
    ]

def test_generated_submission_validity():
    df = pd.read_csv("outputs/submission.csv")
    assert list(df.columns) == OUTPUT_COLUMNS
    assert set(df["flagged"].unique()).issubset({"Yes", "No", "No (justified)"})

    # Check decimal formatting for cost_per_tonne_km
    for cost in df["cost_per_tonne_km"]:
        # Should be parseable float with at most 2 decimal digits
        parts = str(cost).split(".")
        if len(parts) == 2:
            assert len(parts[1]) <= 2
