"""Sales analysis page."""

from __future__ import annotations

import streamlit as st

from ..state import get_state
from ..services import sales_repo
from ..core.data_processing import compute_actual_sales, compute_main_kpis
from ..ui.components import render_kpis, sales_table, filter_bar
from ..ui.charts import sales_by_product
from ..utils.constants import PRODUCTS_DICT, MONTHS


def render() -> None:
    """Render the sales analysis page."""
    st.title("Sales Analysis")
    state = get_state()
    filters = filter_bar(PRODUCTS_DICT.values(), MONTHS)
    state.product = filters["product"]
    state.month = filters["month"]

    df = sales_repo.fetch_sales(limit=1000, product=state.product, month=state.month)
    df = compute_actual_sales(df)
    kpis = compute_main_kpis(df)
    render_kpis(kpis)
    if not df.empty:
        st.plotly_chart(sales_by_product(df))
        sales_table(df)
