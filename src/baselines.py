import pandas as pd
import numpy as np

def compute_own_history_baseline(df_weekly: pd.DataFrame, trailing_weeks: int = 8) -> pd.DataFrame:
    """
    Computes trailing rolling average of cost_per_tonne_km for each route
    strictly before the current week.
    If fewer than 8 prior weeks exist, uses all available prior weeks (min_periods=1).
    If 0 prior weeks exist, result is NaN.
    """
    df = df_weekly.sort_values(["route", "week_of"]).copy()

    # shift(1) ensures we only look strictly at weeks before the current week
    df["own_history_baseline"] = (
        df.groupby("route")["cost_per_tonne_km"]
        .transform(lambda s: s.shift(1).rolling(trailing_weeks, min_periods=1).mean())
    )

    df["vs_own_history_pct"] = np.where(
        df["own_history_baseline"].notna() & (df["own_history_baseline"] > 0),
        ((df["cost_per_tonne_km"] - df["own_history_baseline"]) / df["own_history_baseline"]) * 100.0,
        np.nan
    )

    df["vs_own_history"] = df["vs_own_history_pct"].apply(
        lambda p: f"{p:+.1f}% vs this route's past average" if pd.notna(p) else ""
    )

    return df

def compute_similar_routes_baseline(df_weekly: pd.DataFrame) -> pd.DataFrame:
    """
    Computes peer baseline for each route-week:
    - Same week_of
    - Same route_type
    - Excludes the route itself
    If no peers exist, baseline is NaN.
    """
    df = df_weekly.copy()

    # Aggregate sum and count per (week_of, route_type)
    peer_agg = df.groupby(["week_of", "route_type"]).agg(
        group_sum=("cost_per_tonne_km", "sum"),
        group_count=("cost_per_tonne_km", "count")
    ).reset_index()

    df = df.merge(peer_agg, on=["week_of", "route_type"], how="left")

    # Exclude self
    peer_sum = df["group_sum"] - df["cost_per_tonne_km"]
    peer_count = df["group_count"] - 1

    df["similar_routes_baseline"] = np.where(
        peer_count > 0,
        peer_sum / peer_count,
        np.nan
    )

    df["vs_similar_routes_pct"] = np.where(
        df["similar_routes_baseline"].notna() & (df["similar_routes_baseline"] > 0),
        ((df["cost_per_tonne_km"] - df["similar_routes_baseline"]) / df["similar_routes_baseline"]) * 100.0,
        np.nan
    )

    df["vs_similar_routes"] = df["vs_similar_routes_pct"].apply(
        lambda p: f"{p:+.1f}% vs similar-length routes this week" if pd.notna(p) else ""
    )

    # Drop temporary aggregation columns
    df = df.drop(columns=["group_sum", "group_count"])

    return df

def compute_all_baselines(df_weekly: pd.DataFrame, trailing_weeks: int = 8) -> pd.DataFrame:
    """
    Runs both own-history and similar-routes baseline computations.
    """
    df = compute_own_history_baseline(df_weekly, trailing_weeks=trailing_weeks)
    df = compute_similar_routes_baseline(df)
    return df
