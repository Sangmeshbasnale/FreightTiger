import pandas as pd
from datetime import timedelta

def compute_weekly_route_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes weekly route-level metrics adhering to:
    - route = origin + '-' + destination
    - week_of = Monday of the week (Monday to Sunday)
    - total_tonne_km = sum(quantity_tonnes * distance_km)
    - cost_per_tonne_km = sum(freight_cost_inr) / sum(quantity_tonnes * distance_km)
    """
    df = df.copy()
    if "route" not in df.columns:
        df["route"] = df["origin"].str.strip() + "-" + df["destination"].str.strip()

    # Parse dates and compute Monday week_of
    df["shipment_date_dt"] = pd.to_datetime(df["shipment_date"])
    # In python datetime / pandas, Monday is weekday 0, Sunday is weekday 6
    df["week_of_dt"] = df["shipment_date_dt"] - pd.to_timedelta(df["shipment_date_dt"].dt.weekday, unit="D")
    df["week_of"] = df["week_of_dt"].dt.strftime("%Y-%m-%d")

    df["tonne_km"] = df["quantity_tonnes"] * df["distance_km"]

    # Group by route, route_type, week_of
    weekly = df.groupby(["route", "route_type", "week_of"]).agg(
        total_freight_cost=("freight_cost_inr", "sum"),
        total_tonne_km=("tonne_km", "sum"),
        shipment_count=("shipment_id", "count")
    ).reset_index()

    # Compute unrounded cost_per_tonne_km
    weekly["cost_per_tonne_km"] = weekly["total_freight_cost"] / weekly["total_tonne_km"]

    # Sort deterministically
    weekly = weekly.sort_values(["route", "week_of"]).reset_index(drop=True)

    return weekly
