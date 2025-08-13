from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Ensure the app package is importable when running tests directly
sys.path.append(str(Path(__file__).resolve().parents[1] / "app"))

from core.data_processing import compute_actual_sales


def test_compute_actual_sales_basic() -> None:
    data = [
        {
            "distributor": "D1",
            "product_name": "P1",
            "quantity": 10,
            "year": 2024,
            "month": 5,
            "decade": "10",
            "city": "Kyiv",
            "street": "Main",
            "house_number": "1",
            "new_client": "no",
        },
        {
            "distributor": "D1",
            "product_name": "P1",
            "quantity": 25,
            "year": 2024,
            "month": 5,
            "decade": "20",
            "city": "Kyiv",
            "street": "Main",
            "house_number": "1",
            "new_client": "no",
        },
    ]
    df = pd.DataFrame(data)
    result = compute_actual_sales(df)
    assert result.loc[result["decade"] == "10", "actual_quantity"].iloc[0] == 10
    assert result.loc[result["decade"] == "20", "actual_quantity"].iloc[0] == 15
