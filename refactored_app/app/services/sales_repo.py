"""Data access layer for sales."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from .supabase_client import get_supabase


SCHEMA: Dict[str, str] = {
    "year": "int64",
    "month": "int64",
    "decade": "int64",
    "quantity": "float64",
    "revenue": "float64",
}
CATEGORICAL_COLUMNS = [
    "distributor",
    "product_name",
    "city",
    "street",
    "house_number",
    "new_client",
]


def fetch_sales(limit: int = 1000, offset: int = 0, **filters: Any) -> pd.DataFrame:
    """Fetch sales rows from Supabase with pagination and optional filters."""
    client = get_supabase()
    query = client.table("sales").select("*").range(offset, offset + limit - 1)
    for key, value in filters.items():
        query = query.eq(key, value)
    response = query.execute()
    data = response.data or []
    df = pd.DataFrame(data)
    if df.empty:
        return df
    for col, dtype in SCHEMA.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
    for col in CATEGORICAL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("category")
    return df
