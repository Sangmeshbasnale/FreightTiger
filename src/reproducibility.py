from pathlib import Path
import pandas as pd
from typing import List, Tuple, Dict, Any

def compare_runs(run_paths: List[str]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Compares CSV files produced across multiple runs to verify 100% determinism.
    Returns (is_all_identical, formatted_report, summary_dict).
    """
    if len(run_paths) < 2:
        raise ValueError("At least 2 run paths are required for comparison.")

    dfs = []
    for p in run_paths:
        path_obj = Path(p)
        if not path_obj.exists():
            raise FileNotFoundError(f"Run file does not exist: {p}")
        dfs.append(pd.read_csv(path_obj))

    report_lines = [
        "=== REPRODUCIBILITY COMPARISON REPORT ===",
        f"Comparing {len(run_paths)} runs:"
    ]
    for i, p in enumerate(run_paths):
        report_lines.append(f"  Run {i+1}: {p} ({len(dfs[i])} rows)")
    report_lines.append("")

    all_pairs_identical = True
    pair_results = {}

    for i in range(len(dfs)):
        for j in range(i + 1, len(dfs)):
            pair_name = f"Run {i+1} vs Run {j+1}"

            # Check shape equality first
            if dfs[i].shape != dfs[j].shape:
                pair_results[pair_name] = False
                report_lines.append(f"{pair_name} Identical: False (Shape mismatch: {dfs[i].shape} vs {dfs[j].shape})")
                all_pairs_identical = False
                continue

            # Check column names
            if list(dfs[i].columns) != list(dfs[j].columns):
                pair_results[pair_name] = False
                report_lines.append(f"{pair_name} Identical: False (Column mismatch)")
                all_pairs_identical = False
                continue

            # Check cell-by-cell equality
            diff = dfs[i].compare(dfs[j])
            is_identical = diff.empty
            pair_results[pair_name] = is_identical
            report_lines.append(f"{pair_name} Identical: {is_identical}")
            if not is_identical:
                all_pairs_identical = False

    verdict = "100% REPRODUCIBLE (ZERO DIFF)" if all_pairs_identical else "DIFF DETECTED"
    report_lines.append(f"\nOverall Determinism Verdict: {verdict}")

    report_text = "\n".join(report_lines)
    summary = {
        "all_identical": all_pairs_identical,
        "runs_compared": run_paths,
        "pair_results": pair_results,
        "verdict": verdict
    }
    return all_pairs_identical, report_text, summary
