import sys
from pathlib import Path
import pandas as pd

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config
from src.data_loader import load_raw_data
from src.data_quality import profile_and_validate_shipments
from src.weekly_features import compute_weekly_route_features

def main():
    print("=" * 60)
    print(">>> RUNNING PHASE 2: WEEKLY ROUTE-LEVEL COST COMPUTATION")
    print("=" * 60)

    config = load_config()
    df_shipments, _ = load_raw_data(
        config["data"]["shipments_file"],
        config["data"]["context_notes_file"]
    )
    df_clean, _ = profile_and_validate_shipments(df_shipments)

    print(f"\n1. Aggregating {len(df_clean)} shipments into Monday-to-Sunday weeks...")
    df_weekly = compute_weekly_route_features(df_clean)

    out_file = Path("outputs/route_week_features.csv")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    df_weekly.to_csv(out_file, index=False)

    print(f"2. Saved weekly features to: {out_file}")
    print(f"   Total route-week records generated: {len(df_weekly)}")

    print("\n3. Route-Week breakdown:")
    for route, grp in df_weekly.groupby("route"):
        print(f"   - {route} ({grp['route_type'].iloc[0]}): {len(grp)} weeks | Min cost: {grp['cost_per_tonne_km'].min():.2f} INR | Max cost: {grp['cost_per_tonne_km'].max():.2f} INR | Avg: {grp['cost_per_tonne_km'].mean():.2f} INR")

    print("\n4. Sample 5 route-week feature rows:")
    print(df_weekly[["route", "route_type", "week_of", "total_freight_cost", "total_tonne_km", "shipment_count", "cost_per_tonne_km"]].head(5).to_string(index=False))

    print("\n[PHASE 2 COMPLETE] Weekly route metrics successfully validated.")

if __name__ == "__main__":
    main()
