import argparse
import sys
from pathlib import Path

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import run_shipping_cost_assistant
from src.token_cost_logger import log_token_and_cost

def main():
    parser = argparse.ArgumentParser(description="Run FreightTiger Shipping Cost Assistant")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML")
    parser.add_argument("--output", default="outputs/submission.csv", help="Path to output CSV")
    parser.add_argument("--mode", default=None, choices=["all_route_weeks", "anomalies_only"], help="Output mode")
    parser.add_argument("--log-cost", action="store_true", help="Generate token and cost log upon completion")
    args = parser.parse_args()

    print(f"Starting FreightTiger Shipping Cost Assistant...")
    df, out_path = run_shipping_cost_assistant(
        config_path=args.config,
        output_override=args.output
    )

    print(f"\nPipeline successfully completed! Output saved to: {out_path}")
    print("\n=== SUMMARY STATISTICS ===")
    print(f"Total route-weeks computed: {len(df)}")
    print("Flag distribution:")
    print(df["flagged"].value_counts().to_string())
    print("\nJustified cases matched:")
    justified = df[df["matched_note_id"] != ""]
    if not justified.empty:
        for _, j in justified.iterrows():
            print(f"  - Route: {j['route']}, Week: {j['week_of']}, Note: {j['matched_note_id']}, Cost: {j['cost_per_tonne_km']:.2f}")
    else:
        print("  None")

    if args.log_cost:
        print("\nLogging token & cost usage...")
        log_token_and_cost()
        print("Logged to outputs/token_cost_log.json")

if __name__ == "__main__":
    main()
