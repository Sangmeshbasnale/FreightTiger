import pytest
import pandas as pd
from src.anomaly_policy import identify_anomaly_candidates

def test_anomaly_flagging_own_threshold():
    # If cost is rising vs own history and >= own_pct_threshold, must flag
    config = {
        "flagging": {
            "own_pct_threshold": 8.0,
            "peer_pct_threshold": 15.0,
            "no_history_peer_pct_threshold": 25.0,
            "require_positive_own_if_available": True
        }
    }
    df = pd.DataFrame([
        {
            "route": "Delhi-Jaipur", "week_of": "2024-05-06",
            "cost_per_tonne_km": 3.5, "own_history_baseline": 3.0,
            "vs_own_history_pct": 16.67, "similar_routes_baseline": 3.4,
            "vs_similar_routes_pct": 2.94
        },
        {
            "route": "Delhi-Jaipur", "week_of": "2024-05-13",
            "cost_per_tonne_km": 3.1, "own_history_baseline": 3.0,
            "vs_own_history_pct": 3.33, "similar_routes_baseline": 3.2,
            "vs_similar_routes_pct": -3.12
        }
    ])
    res = identify_anomaly_candidates(df, config)
    assert res.iloc[0]["is_anomaly_candidate"] == True
    assert res.iloc[1]["is_anomaly_candidate"] == False

def test_anomaly_flagging_require_positive_own():
    # If cost is LOWER than own baseline, even if peer diff is high, require_positive_own prevents flagging
    config = {
        "flagging": {
            "own_pct_threshold": 8.0,
            "peer_pct_threshold": 15.0,
            "require_positive_own_if_available": True
        }
    }
    df = pd.DataFrame([
        {
            "route": "Mumbai-Pune", "week_of": "2024-06-03",
            "cost_per_tonne_km": 3.0, "own_history_baseline": 3.5,
            "vs_own_history_pct": -14.28, "similar_routes_baseline": 2.5,
            "vs_similar_routes_pct": 20.0
        }
    ])
    res = identify_anomaly_candidates(df, config)
    assert res.iloc[0]["is_anomaly_candidate"] == False

def test_anomaly_flagging_first_week_no_history():
    # First week (no own history): flags if peer pct >= no_history_peer_pct_threshold (25.0%)
    config = {
        "flagging": {
            "no_history_peer_pct_threshold": 25.0
        }
    }
    df = pd.DataFrame([
        {
            "route": "Delhi-Chennai", "week_of": "2024-01-01",
            "cost_per_tonne_km": 3.0, "own_history_baseline": None,
            "vs_own_history_pct": None, "similar_routes_baseline": 2.0,
            "vs_similar_routes_pct": 50.0
        },
        {
            "route": "Delhi-Chennai", "week_of": "2024-01-08",
            "cost_per_tonne_km": 2.2, "own_history_baseline": None,
            "vs_own_history_pct": None, "similar_routes_baseline": 2.0,
            "vs_similar_routes_pct": 10.0
        }
    ])
    res = identify_anomaly_candidates(df, config)
    assert res.iloc[0]["is_anomaly_candidate"] == True
    assert res.iloc[1]["is_anomaly_candidate"] == False
