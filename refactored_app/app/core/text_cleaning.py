"""Utilities for cleaning text data and building addresses."""

from __future__ import annotations

import unicodedata
from typing import Iterable

import pandas as pd


def _normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value.strip()) if value else ""


def clean_text_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Strip and normalize text columns in ``df``."""
    for col in columns:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).map(_normalize)
    return df


def create_full_address(df: pd.DataFrame) -> pd.DataFrame:
    """Create ``full_address`` column from city, street and house number."""
    if "full_address" not in df.columns:
        parts = df[["city", "street", "house_number"]].fillna("").astype(str)
        df["full_address"] = (
            (parts["city"] + ", " + parts["street"] + ", " + parts["house_number"])
            .str.replace(r"(, )+", ", ", regex=True)
            .str.strip(" ,")
        )
    return df
