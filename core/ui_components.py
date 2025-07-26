import streamlit as st
import pandas as pd

def display_kpi_card(title: str, value: str, help_text: str = ""):
    """Відображає стильну картку KPI з можливістю додати підказку."""
    st.metric(label=title, value=value, help=help_text)

def render_local_filters(df: pd.DataFrame, key_prefix: str) -> tuple:
    """
    Створює локальні фільтри для міста та вулиці.
    Повертає обрані значення.
    """

    filter_cols = st.columns(2)

    with filter_cols[0]:
        unique_cities = ["Всі"] + sorted(df['city'].dropna().unique().tolist())
        selected_city = st.selectbox(
            "Місто:", unique_cities, key=f"{key_prefix}_city_filter"
        )

    with filter_cols[1]:
        if selected_city != "Всі":
            streets_in_city = df[df['city'] == selected_city]['street'].dropna().unique()
            unique_streets = ["Всі"] + sorted(streets_in_city.tolist())
        else:
            unique_streets = ["Всі"] + sorted(df['street'].dropna().unique().tolist())
        selected_street = st.selectbox(
            "Вулиця:", unique_streets, key=f"{key_prefix}_street_filter"
        )

    return selected_city, selected_street

def apply_filters(df: pd.DataFrame, city: str, street: str) -> pd.DataFrame:
    """Застосовує фільтри до DataFrame."""
    filtered_df = df.copy()
    if city != "Всі":
        filtered_df = filtered_df[filtered_df['city'] == city]
    if street != "Всі":
        filtered_df = filtered_df[filtered_df['street'] == street]
    return filtered_df
