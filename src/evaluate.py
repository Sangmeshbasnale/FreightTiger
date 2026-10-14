import json
from pathlib import Path
import pandas as pd
from typing import Dict, Any, List
from src.output_writer import OUTPUT_COLUMNS

TRAP_NOTES = ["N004", "N005", "N006", "N007", "N008", "N009", "N010"]

DEFAULT_BENCHMARKS = [
    {
        "route": "Delhi-Jaipur",
        "week_of": "2024-11-11",
        "expected_flag": "Yes",
        "expected_note": "",
        "description": "Sample row 1: Unexplained spike"
    },
    {
        "route": "Ahmedabad-Mumbai",
        "week_of": "2025-01-20",
        "expected_flag": "No (justified)",
        "expected_note": "N002",
        "description": "Sample row 2: Festival week surcharge"
    },
    {
        "route": "Mumbai-Pune",
        "week_of": "2025-09-15",
        "expected_flag": "Yes",
        "expected_note": "",
        "description": "Sample row 3: Spike near non-justifying note N006"
    },
    {
        "route": "Chennai-Bangalore",
        "week_of": "2025-02-24",
        "expected_flag": "No (justified)",
        "expected_note": "N001",
        "description": "Ground truth: Highway flooding start"
    },
    {
        "route": "Chennai-Bangalore",
        "week_of": "2025-03-03",
        "expected_flag": "No (justified)",
        "expected_note": "N001",
        "description": "Ground truth: Highway flooding week 2"
    }
]

def evaluate_submission(
    submission_path: str = "outputs/submission.csv",
    benchmarks: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates the submission CSV against schema, golden benchmarks, and negative control trap notes.
    """
    benchmarks = benchmarks or DEFAULT_BENCHMARKS
    sub_file = Path(submission_path)
    if not sub_file.exists():
        raise FileNotFoundError(f"Submission file does not exist at {submission_path}")

    df = pd.read_csv(sub_file)

    report = {
        "submission_file": str(sub_file),
        "total_rows": len(df),
        "schema_valid": True,
        "golden_benchmarks_passed": 0,
        "golden_benchmarks_total": len(benchmarks),
        "golden_benchmark_results": [],
        "negative_controls_passed": True,
        "trap_notes_detected": [],
        "overall_status": "PASSED"
    }

    # 1. Schema check
    if list(df.columns) != OUTPUT_COLUMNS:
        report["schema_valid"] = False
        report["overall_status"] = "FAILED"

    # 2. Golden benchmarks
    for bench in benchmarks:
        match = df[(df["route"] == bench["route"]) & (df["week_of"] == bench["week_of"])]
        if match.empty:
            result = {
                "route": bench["route"],
                "week_of": bench["week_of"],
                "passed": False,
                "error": "Row not found"
            }
            report["overall_status"] = "FAILED"
        else:
            row = match.iloc[0]
            gen_flag = str(row["flagged"]).strip()
            gen_note = str(row["matched_note_id"]).strip() if pd.notna(row["matched_note_id"]) else ""

            flag_ok = (gen_flag == bench["expected_flag"])
            note_ok = (gen_note == bench["expected_note"])
            passed = flag_ok and note_ok

            result = {
                "route": bench["route"],
                "week_of": bench["week_of"],
                "expected_flag": bench["expected_flag"],
                "actual_flag": gen_flag,
                "expected_note": bench["expected_note"],
                "actual_note": gen_note,
                "passed": passed,
                "description": bench["description"]
            }
            if passed:
                report["golden_benchmarks_passed"] += 1
            else:
                report["overall_status"] = "FAILED"
        report["golden_benchmark_results"].append(result)

    # 3. Negative controls
    matched_notes_in_df = df["matched_note_id"].dropna().unique().tolist()
    for trap in TRAP_NOTES:
        if trap in matched_notes_in_df:
            report["trap_notes_detected"].append(trap)
            report["negative_controls_passed"] = False
            report["overall_status"] = "FAILED"

    out_eval = Path("outputs/eval_report.json")
    out_eval.parent.mkdir(parents=True, exist_ok=True)
    with open(out_eval, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report
