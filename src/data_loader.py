from pathlib import Path
import pandas as pd
from typing import Tuple

def load_raw_data(
    shipments_path: str = "shipment_records.csv",
    notes_path: str = "context_notes.csv"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads raw shipments and context notes CSVs.
    Checks data/raw/, data/, or workspace root.
    """
    def find_file(filename: str) -> Path:
        candidates = [
            Path("data/raw") / filename,
            Path("data") / filename,
            Path(filename)
        ]
        for c in candidates:
            if c.exists():
                return c
        raise FileNotFoundError(f"File '{filename}' not found in data/raw/, data/, or ./")

    s_file = find_file(Path(shipments_path).name)
    n_file = find_file(Path(notes_path).name)

    df_shipments = pd.read_csv(s_file)
    df_notes = pd.read_csv(n_file)

    return df_shipments, df_notes
