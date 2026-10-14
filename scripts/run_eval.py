import sys
from pathlib import Path

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluate import evaluate_submission

def main():
    print("=" * 60)
    print(">>> RUNNING EVALUATION HARNESS (PHASE 7)")
    print("=" * 60)
    report = evaluate_submission("outputs/submission.csv")

    print("\n=== EVALUATION REPORT ===")
    print(f"Overall Status: {report['overall_status']}")
    print(f"Schema Valid: {report['schema_valid']}")
    print(f"Golden Benchmarks Passed: {report['golden_benchmarks_passed']}/{report['golden_benchmarks_total']}")
    for r in report["golden_benchmark_results"]:
        status_sym = "[PASS]" if r["passed"] else "[FAIL]"
        print(f"  {status_sym} {r['route']} ({r['week_of']}): Flag='{r.get('actual_flag')}', Note='{r.get('actual_note')}' - {r['description']}")

    print(f"\nNegative Controls Passed: {report['negative_controls_passed']}")
    if report["trap_notes_detected"]:
        print(f"  WARNING: Trap notes detected: {report['trap_notes_detected']}")
    else:
        print("  Zero trap notes were matched (all 7 non-justifying notes correctly filtered).")

    print("\nReport written to outputs/eval_report.json")

if __name__ == "__main__":
    main()
