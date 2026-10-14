import pytest
import pandas as pd
from pathlib import Path
from src.reproducibility import compare_runs

def test_compare_runs_identical(tmp_path):
    df = pd.DataFrame({
        "route": ["Delhi-Jaipur", "Mumbai-Pune"],
        "week_of": ["2024-01-01", "2024-01-01"],
        "cost": [3.12, 4.50]
    })
    p1 = tmp_path / "run1.csv"
    p2 = tmp_path / "run2.csv"
    df.to_csv(p1, index=False)
    df.to_csv(p2, index=False)

    identical, report, summary = compare_runs([str(p1), str(p2)])
    assert identical is True
    assert summary["all_identical"] is True
    assert "100% REPRODUCIBLE" in summary["verdict"]

def test_compare_runs_different_values(tmp_path):
    df1 = pd.DataFrame({"route": ["Delhi-Jaipur"], "cost": [3.12]})
    df2 = pd.DataFrame({"route": ["Delhi-Jaipur"], "cost": [3.15]})
    p1 = tmp_path / "run1.csv"
    p2 = tmp_path / "run2.csv"
    df1.to_csv(p1, index=False)
    df2.to_csv(p2, index=False)

    identical, report, summary = compare_runs([str(p1), str(p2)])
    assert identical is False
    assert summary["all_identical"] is False
    assert "DIFF DETECTED" in summary["verdict"]

def test_compare_runs_shape_mismatch(tmp_path):
    df1 = pd.DataFrame({"route": ["Delhi-Jaipur", "Mumbai-Pune"], "cost": [3.12, 4.5]})
    df2 = pd.DataFrame({"route": ["Delhi-Jaipur"], "cost": [3.12]})
    p1 = tmp_path / "run1.csv"
    p2 = tmp_path / "run2.csv"
    df1.to_csv(p1, index=False)
    df2.to_csv(p2, index=False)

    identical, report, summary = compare_runs([str(p1), str(p2)])
    assert identical is False
    assert summary["all_identical"] is False
    assert "Shape mismatch" in report
