import os
import yaml
from pathlib import Path

DEFAULT_CONFIG = {
    "data": {
        "shipments_file": "shipment_records.csv",
        "context_notes_file": "context_notes.csv",
        "sample_output_file": "sample_output_format_v2.csv"
    },
    "baseline": {
        "trailing_weeks": 8,
        "min_prior_weeks": 1
    },
    "flagging": {
        "own_pct_threshold": 8.0,
        "peer_pct_threshold": 15.0,
        "no_history_peer_pct_threshold": 25.0,
        "require_positive_own_if_available": True
    },
    "retrieval": {
        "model_name": "all-MiniLM-L6-v2",
        "top_k": 3
    },
    "output": {
        "mode": "all_route_weeks",
        "output_file": "outputs/submission.csv"
    }
}

def load_config(config_path: str = "config.yaml") -> dict:
    path = Path(config_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f)
            # merge with defaults
            config = DEFAULT_CONFIG.copy()
            if user_config:
                for k, v in user_config.items():
                    if isinstance(v, dict) and k in config and isinstance(config[k], dict):
                        config[k].update(v)
                    else:
                        config[k] = v
            return config
    return DEFAULT_CONFIG.copy()
