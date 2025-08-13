"""Charts with a unified theme."""

from __future__ import annotations

import pandas as pd
import plotly.express as px

_theme = {"template": "plotly_white", "colorway": px.colors.qualitative.Set2}


def sales_by_product(df: pd.DataFrame):
    """Return a bar chart of sales by product."""
    fig = px.bar(
        df,
        x="product_name",
        y="actual_quantity",
        color="product_name",
        template=_theme["template"],
        color_discrete_sequence=_theme["colorway"],
    )
    return fig
