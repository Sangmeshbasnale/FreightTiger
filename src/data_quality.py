import json
from pathlib import Path
import pandas as pd
from typing import Tuple, Dict, Any

REQUIRED_COLUMNS = [
    "shipment_id", "origin", "destination", "route_type",
    "material", "quantity_tonnes", "distance_km",
    "freight_cost_inr", "shipment_date", "transporter"
]

def profile_and_validate_shipments(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    report: Dict[str, Any] = {
        "total_records": len(df),
        "missing_columns": [],
        "null_counts": {},
        "invalid_quantity_count": 0,
        "invalid_distance_count": 0,
        "invalid_cost_count": 0,
        "invalid_date_count": 0,
        "duplicate_shipment_ids": 0,
        "routes_found": [],
        "route_types_by_route": {},
        "date_range": {},
        "clean_records_count": 0,
        "dropped_records_count": 0
    }

    # 1. Missing columns check
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            report["missing_columns"].append(col)
    if report["missing_columns"]:
        raise ValueError(f"Shipment records missing required columns: {report['missing_columns']}")

    # 2. Null counts
    for col in REQUIRED_COLUMNS:
        null_cnt = int(df[col].isna().sum())
        if null_cnt > 0:
            report["null_counts"][col] = null_cnt

    # 3. Duplicate shipment IDs
    report["duplicate_shipment_ids"] = int(df["shipment_id"].duplicated().sum())

    # 4. Data type & value validity masks
    valid_qty = pd.to_numeric(df["quantity_tonnes"], errors="coerce") > 0
    report["invalid_quantity_count"] = int((~valid_qty).sum())

    valid_dist = pd.to_numeric(df["distance_km"], errors="coerce") > 0
    report["invalid_distance_count"] = int((~valid_dist).sum())

    valid_cost = pd.to_numeric(df["freight_cost_inr"], errors="coerce") >= 0
    report["invalid_cost_count"] = int((~valid_cost).sum())

    parsed_dates = pd.to_datetime(df["shipment_date"], errors="coerce")
    valid_date = parsed_dates.notna()
    report["invalid_date_count"] = int((~valid_date).sum())

    clean_mask = valid_qty & valid_dist & valid_cost & valid_date
    df_clean = df[clean_mask].copy()
    report["clean_records_count"] = len(df_clean)
    report["dropped_records_count"] = len(df) - len(df_clean)

    # 5. Enrich route and check consistency
    df_clean["route"] = df_clean["origin"].str.strip() + "-" + df_clean["destination"].str.strip()
    routes = sorted(df_clean["route"].unique().tolist())
    report["routes_found"] = routes

    route_types = {}
    for r in routes:
        types = df_clean[df_clean["route"] == r]["route_type"].unique().tolist()
        route_types[r] = types
    report["route_types_by_route"] = route_types

    # 6. Date range
    clean_dates = pd.to_datetime(df_clean["shipment_date"])
    report["date_range"] = {
        "min_date": str(clean_dates.min().date()),
        "max_date": str(clean_dates.max().date()),
        "total_days": int((clean_dates.max() - clean_dates.min()).days + 1)
    }

    # Save report
    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "data_quality_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return df_clean, report
