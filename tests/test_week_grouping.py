import pytest
import pandas as pd
from datetime import date
from src.weekly_features import compute_weekly_route_features

def test_monday_week_mapping():
    # 2024-01-01 is Monday -> week_of should be 2024-01-01
    # 2024-01-07 is Sunday -> week_of should be 2024-01-01
    # 2024-01-08 is Monday -> week_of should be 2024-01-08
    sample_data = pd.DataFrame([
        {
            "shipment_id": "S1", "origin": "Delhi", "destination": "Jaipur",
            "route_type": "Short", "material": "Auto", "quantity_tonnes": 10.0,
            "distance_km": 100.0, "freight_cost_inr": 1000.0, "shipment_date": "2024-01-01",
            "transporter": "T1"
        },
        {
            "shipment_id": "S2", "origin": "Delhi", "destination": "Jaipur",
            "route_type": "Short", "material": "Auto", "quantity_tonnes": 20.0,
            "distance_km": 100.0, "freight_cost_inr": 2000.0, "shipment_date": "2024-01-07",
            "transporter": "T1"
        },
        {
            "shipment_id": "S3", "origin": "Delhi", "destination": "Jaipur",
            "route_type": "Short", "material": "Auto", "quantity_tonnes": 10.0,
            "distance_km": 100.0, "freight_cost_inr": 1500.0, "shipment_date": "2024-01-08",
            "transporter": "T1"
        }
    ])
    result = compute_weekly_route_features(sample_data)
    weeks = sorted(result["week_of"].unique().tolist())
    assert weeks == ["2024-01-01", "2024-01-08"]

def test_cost_per_tonne_km_formula():
    # Formula must be: sum(cost) / sum(quantity * distance)
    # Shipment 1: cost=1000, qty=10, dist=100 -> tonne_km = 1000
    # Shipment 2: cost=3000, qty=20, dist=100 -> tonne_km = 2000
    # Total cost = 4000, Total tonne_km = 3000 -> cost_per_tonne_km = 4000 / 3000 = 1.333333...
    sample_data = pd.DataFrame([
        {
            "shipment_id": "S1", "origin": "Mumbai", "destination": "Pune",
            "route_type": "Short", "material": "Cement", "quantity_tonnes": 10.0,
            "distance_km": 100.0, "freight_cost_inr": 1000.0, "shipment_date": "2024-01-02",
            "transporter": "T1"
        },
        {
            "shipment_id": "S2", "origin": "Mumbai", "destination": "Pune",
            "route_type": "Short", "material": "Cement", "quantity_tonnes": 20.0,
            "distance_km": 100.0, "freight_cost_inr": 3000.0, "shipment_date": "2024-01-03",
            "transporter": "T1"
        }
    ])
    result = compute_weekly_route_features(sample_data)
    assert len(result) == 1
    assert pytest.approx(result.iloc[0]["cost_per_tonne_km"], 0.0001) == 4000.0 / 3000.0
