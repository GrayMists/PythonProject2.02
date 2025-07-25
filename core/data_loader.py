import streamlit as st
import pandas as pd
from utils import supabase


@st.cache_data(ttl=3600)
### <<< ЗМІНА 1: ДОДАНО 'region_name' В АРГУМЕНТИ ФУНКЦІЇ >>>
def fetch_all_sales_data(region_name: str, territory: str, line: str, months: list) -> pd.DataFrame:
    """
    Завантажує дані з таблиці sales_data, використовуючи пагінацію та фільтри.
    """
    all_data = []
    offset = 0
    page_size = 1000

    select_query = "client,new_client, product_name, quantity, city, street, house_number, territory, adding, product_line, delivery_address, year, month, decade"

    while True:
        try:
            query = supabase.table("sales_data").select(select_query).range(offset, offset + page_size - 1)

            ### <<< ЗМІНА 2: ДОДАНО ЛОГІКУ ФІЛЬТРАЦІЇ ЗА РЕГІОНОМ >>>
            # Фільтруємо за назвою регіону, якщо вона обрана
            if region_name and region_name != "Оберіть регіон...":
                # Припущення: колонка в таблиці sales_data називається 'region'
                query = query.eq('region', region_name)

            # Існуючі фільтри
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
            st.error(f"Помилка при завантаженні даних про продажі з Supabase: {e}")
            return pd.DataFrame()

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)
    return df


@st.cache_data(ttl=3600)
def fetch_price_data(months: list[str]) -> pd.DataFrame:
    """
    Завантажує дані про ціни з таблиці 'price' для вказаних місяців.
    """
    if not months:
        return pd.DataFrame()

    try:
        # Конвертуємо рядкові місяці ('06') в числа ([6]) для запиту до бази
        numeric_months = [int(m) for m in months]

        query = supabase.table("price").select("product_name, price, month").in_("month", numeric_months)
        response = query.execute()

        if not response.data:
            return pd.DataFrame()

        price_df = pd.DataFrame(response.data)
        price_df = price_df.drop_duplicates(subset=['product_name', 'month'], keep='last')

        # Конвертуємо типи, але ЗАЛИШАЄМО 'month' ЧИСЛОВИМ для коректного об'єднання
        price_df['price'] = pd.to_numeric(price_df['price'], errors='coerce')
        price_df['month'] = pd.to_numeric(price_df['month'], errors='coerce').astype('Int64')

        return price_df

    except Exception as e:
        st.error(f"Помилка при завантаженні цін з Supabase: {e}")
        return pd.DataFrame()
