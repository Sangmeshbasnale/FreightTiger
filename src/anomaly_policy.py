import pandas as pd
from typing import Dict, Any

def identify_anomaly_candidates(df_baselines: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Identifies rows that have an unusual cost rise.
    Returns the dataframe with an additional boolean column 'is_anomaly_candidate'.
    """
    flag_cfg = config.get("flagging", {})
    own_thresh = flag_cfg.get("own_pct_threshold", 8.0)
    peer_thresh = flag_cfg.get("peer_pct_threshold", 15.0)
    no_hist_peer_thresh = flag_cfg.get("no_history_peer_pct_threshold", 25.0)
    req_pos_own = flag_cfg.get("require_positive_own_if_available", True)

    df = df_baselines.copy()

    def check_candidate(row) -> bool:
        has_own = pd.notna(row["own_history_baseline"])
        has_peer = pd.notna(row["similar_routes_baseline"])

        if has_own:
            rising_vs_own = row["cost_per_tonne_km"] > row["own_history_baseline"]
            if req_pos_own and not rising_vs_own:
                return False

            own_flag = pd.notna(row["vs_own_history_pct"]) and (row["vs_own_history_pct"] >= own_thresh)
            peer_flag = pd.notna(row["vs_similar_routes_pct"]) and (row["vs_similar_routes_pct"] >= peer_thresh)

            return bool(own_flag or peer_flag)
        else:
            if has_peer:
                return bool(pd.notna(row["vs_similar_routes_pct"]) and (row["vs_similar_routes_pct"] >= no_hist_peer_thresh))
            return False

    df["is_anomaly_candidate"] = df.apply(check_candidate, axis=1)
    return df
