"""Reusable UI components."""

from __future__ import annotations

from typing import Iterable, Any, Dict

import pandas as pd
import streamlit as st


def render_kpis(kpis: Dict[str, float]) -> None:
    """Render KPI metrics using Streamlit."""
    cols = st.columns(len(kpis))
    for col, (label, value) in zip(cols, kpis.items()):
        col.metric(label, f"{value:.2f}")


def filter_bar(products: Iterable[str], months: Iterable[int]) -> Dict[str, Any]:
    """Render product and month filters and return selections."""
    with st.sidebar:
        product = st.selectbox("Product", ["All", *products])
        month = st.selectbox("Month", months)
    return {"product": None if product == "All" else product, "month": month}


def sales_table(df: pd.DataFrame) -> None:
    """Display sales table."""
    st.dataframe(df)
