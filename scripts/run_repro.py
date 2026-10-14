import sys
from pathlib import Path

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import run_shipping_cost_assistant
from src.reproducibility import compare_runs

def main():
    print("=" * 60)
    print(">>> RUNNING 3-RUN REPRODUCIBILITY VERIFICATION (PHASE 8)")
    print("=" * 60)
    print("Executing 3 untouched reproducibility runs from raw data...")

    run_paths = [
        "outputs/run_1/submission.csv",
        "outputs/run_2/submission.csv",
        "outputs/run_3/submission.csv"
    ]

    for i, path in enumerate(run_paths, start=1):
        print(f"\n--- Running Run {i} ---")
        _, saved_path = run_shipping_cost_assistant(output_override=path)
        print(f"Run {i} complete: {saved_path}")

    identical, report_text, summary = compare_runs(run_paths)
    print("\n" + report_text)

    out_file = Path("outputs/repro_report.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\nReport written to: {out_file}")

if __name__ == "__main__":
    main()
