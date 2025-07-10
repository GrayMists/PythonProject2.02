import streamlit as st
import pandas as pd
from utils import supabase

@st.cache_data(ttl=3600)
def fetch_all_sales_data(territory: str, line: str, months: list) -> pd.DataFrame:
    """
    Завантажує дані з таблиці sales_data, використовуючи пагінацію.
    Функція ізольована і відповідає лише за отримання даних.
    """
    all_data = []
    offset = 0
    page_size = 1000  # Supabase має ліміт у 1000 записів за раз

    select_query = "client, product_name, quantity, city, street, house_number, territory, adding, product_line, delivery_address, year, month, decade"

    while True:
        try:
            query = supabase.table("sales_data").select(select_query).range(offset, offset + page_size - 1)

            if territory != "Всі":
                query = query.eq("territory", territory)
            if line != "Всі":
                query = query.eq("product_line", line)
            if months:
                query = query.in_("month", months)

            response = query.execute()

            if response.data:
                all_data.extend(response.data)
                if len(response.data) < page_size:
                    break
                offset += page_size
            else:
                break
        except Exception as e:
            st.error(f"Помилка при завантаженні даних з Supabase: {e}")
            return pd.DataFrame()

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    # Базова конвертація типів одразу після завантаження
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)
    return df
