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
        unique_cities = sorted(df['city'].dropna().unique().tolist())
        selected_cities = st.multiselect(
            "Місто:",
            unique_cities,
            default=[],
            key=f"{key_prefix}_city_filter"
        )

    with filter_cols[1]:
        # якщо вибрані міста – фільтруємо по них
        if selected_cities:
            streets_in_selected_cities = df[df['city'].isin(selected_cities)]['street'].dropna().unique()
            unique_streets = sorted(streets_in_selected_cities.tolist())
        else:
            # якщо не вибрано жодного міста – показуємо всі вулиці
            unique_streets = sorted(df['street'].dropna().unique().tolist())

        selected_streets = st.multiselect(
            "Вулиця:",
            unique_streets,
            default=[],
            key=f"{key_prefix}_street_filter"
        )

    return selected_cities, selected_streets

def apply_filters(df, cities, streets):
    filtered_df = df.copy()
    if cities:  # якщо список не порожній
        filtered_df = filtered_df[filtered_df['city'].isin(cities)]
    if streets:
        filtered_df = filtered_df[filtered_df['street'].isin(streets)]
    return filtered_df