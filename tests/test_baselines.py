import pytest
import pandas as pd
import numpy as np
from src.baselines import compute_own_history_baseline, compute_similar_routes_baseline

def test_own_history_no_lookahead():
    # 3 consecutive weeks for Delhi-Jaipur: costs = 2.0, 4.0, 6.0
    # Week 1: baseline = NaN (no prior weeks)
    # Week 2: baseline = 2.0 (only week 1)
    # Week 3: baseline = mean(2.0, 4.0) = 3.0
    data = pd.DataFrame([
        {"route": "Delhi-Jaipur", "route_type": "Short", "week_of": "2024-01-01", "cost_per_tonne_km": 2.0},
        {"route": "Delhi-Jaipur", "route_type": "Short", "week_of": "2024-01-08", "cost_per_tonne_km": 4.0},
        {"route": "Delhi-Jaipur", "route_type": "Short", "week_of": "2024-01-15", "cost_per_tonne_km": 6.0},
    ])
    res = compute_own_history_baseline(data, trailing_weeks=8)
    assert pd.isna(res.iloc[0]["own_history_baseline"])
    assert res.iloc[0]["vs_own_history"] == ""

    assert res.iloc[1]["own_history_baseline"] == 2.0
    # ((4.0 - 2.0) / 2.0) * 100 = +100.0%
    assert "+100.0% vs this route's past average" in res.iloc[1]["vs_own_history"]

    assert res.iloc[2]["own_history_baseline"] == 3.0
    # ((6.0 - 3.0) / 3.0) * 100 = +100.0%
    assert "+100.0% vs this route's past average" in res.iloc[2]["vs_own_history"]

def test_similar_routes_peer_exclusion():
    # 3 routes in same week with same route_type (Short):
    # Route A: 2.0
    # Route B: 4.0
    # Route C: 6.0
    # For Route A: peers are B and C -> mean(4.0, 6.0) = 5.0 -> vs_peer = ((2.0 - 5.0) / 5.0) * 100 = -60.0%
    # For Route B: peers are A and C -> mean(2.0, 6.0) = 4.0 -> vs_peer = 0.0%
    data = pd.DataFrame([
        {"route": "Route-A", "route_type": "Short", "week_of": "2024-01-01", "cost_per_tonne_km": 2.0},
        {"route": "Route-B", "route_type": "Short", "week_of": "2024-01-01", "cost_per_tonne_km": 4.0},
        {"route": "Route-C", "route_type": "Short", "week_of": "2024-01-01", "cost_per_tonne_km": 6.0},
    ])
    res = compute_similar_routes_baseline(data)
    row_a = res[res["route"] == "Route-A"].iloc[0]
    row_b = res[res["route"] == "Route-B"].iloc[0]

    assert row_a["similar_routes_baseline"] == 5.0
    assert "-60.0% vs similar-length routes this week" in row_a["vs_similar_routes"]

    assert row_b["similar_routes_baseline"] == 4.0
    assert "+0.0% vs similar-length routes this week" in row_b["vs_similar_routes"]
