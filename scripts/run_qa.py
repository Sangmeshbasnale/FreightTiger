import sys
from pathlib import Path
# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config
from src.data_loader import load_raw_data
from src.data_quality import profile_and_validate_shipments

def main():
    config = load_config()
    print("Loading raw data...")
    df_shipments, df_notes = load_raw_data(
        config["data"]["shipments_file"],
        config["data"]["context_notes_file"]
    )
    print(f"Loaded {len(df_shipments)} shipment records, {len(df_notes)} context notes.")

    print("\nRunning profiling and validation...")
    df_clean, report = profile_and_validate_shipments(df_shipments)
    print("\n=== DATA QUALITY SUMMARY ===")
    print(f"Total records: {report['total_records']}")
    print(f"Clean records: {report['clean_records_count']}")
    print(f"Dropped records: {report['dropped_records_count']}")
    print(f"Null counts: {report['null_counts']}")
    print(f"Duplicate IDs: {report['duplicate_shipment_ids']}")
    print(f"Date range: {report['date_range']['min_date']} to {report['date_range']['max_date']} ({report['date_range']['total_days']} days)")
    print(f"Routes found ({len(report['routes_found'])}):")
    for r in report['routes_found']:
        print(f"  - {r}: {report['route_types_by_route'][r]}")

    print("\nReport written to outputs/data_quality_report.json")

if __name__ == "__main__":
    main()
