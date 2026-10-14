import pandas as pd
from typing import Dict, Any, Tuple
from pathlib import Path

from src.config import load_config
from src.data_loader import load_raw_data
from src.data_quality import profile_and_validate_shipments
from src.weekly_features import compute_weekly_route_features
from src.baselines import compute_all_baselines
from src.anomaly_policy import identify_anomaly_candidates
from src.notes_registry import NotesRegistry
from src.retrieval import NoteRetriever
from src.justification import evaluate_justification
from src.explanation import render_normal_reason
from src.output_writer import write_submission_csv

def run_shipping_cost_assistant(
    config_path: str = "config.yaml",
    output_override: str = None
) -> Tuple[pd.DataFrame, Path]:
    """
    Executes the end-to-end Shipping Cost Assistant pipeline and persists
    all intermediate and final artifacts specified in plan.md.
    """
    config = load_config(config_path)
    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    df_shipments, df_notes = load_raw_data(
        config["data"]["shipments_file"],
        config["data"]["context_notes_file"]
    )

    # 2. Quality & Validation
    df_clean, qa_report = profile_and_validate_shipments(df_shipments)

    # 3. Weekly features (Phase 2 artifact)
    df_weekly = compute_weekly_route_features(df_clean)
    df_weekly.to_csv(out_dir / "route_week_features.csv", index=False)
    try:
        df_weekly.to_parquet(out_dir / "route_week_features.parquet", index=False)
    except Exception:
        pass

    # 4. Trailing and Peer baselines (Phase 3 artifact)
    df_baselines = compute_all_baselines(
        df_weekly,
        trailing_weeks=config["baseline"].get("trailing_weeks", 8)
    )
    df_baselines.to_csv(out_dir / "baselines.csv", index=False)
    try:
        df_baselines.to_parquet(out_dir / "baselines.parquet", index=False)
    except Exception:
        pass

    # 5. Flagging policy & candidate detection (Phase 4 artifact)
    df_candidates = identify_anomaly_candidates(df_baselines, config)
    df_candidates.to_csv(out_dir / "anomaly_candidates.csv", index=False)

    # 6. Notes Registry & Semantic Retriever (Phase 5)
    registry = NotesRegistry(df_notes)
    retriever = NoteRetriever(
        registry,
        model_name=config["retrieval"].get("model_name", "all-MiniLM-L6-v2")
    )

    # 7. Justification & Reason Generation (Phase 6)
    flagged_list = []
    matched_notes_list = []
    reasons_list = []

    for _, row in df_candidates.iterrows():
        if row["is_anomaly_candidate"]:
            f, m, r = evaluate_justification(row, retriever)
        else:
            f = "No"
            m = ""
            r = render_normal_reason()
        flagged_list.append(f)
        matched_notes_list.append(m)
        reasons_list.append(r)

    df_candidates["flagged"] = flagged_list
    df_candidates["matched_note_id"] = matched_notes_list
    df_candidates["reason"] = reasons_list

    # 8. Output generation
    out_path = output_override or config["output"].get("output_file", "outputs/submission.csv")
    mode = config["output"].get("mode", "all_route_weeks")
    saved_file = write_submission_csv(df_candidates, output_path=out_path, mode=mode)

    return df_candidates, saved_file
