import streamlit as st
import pandas as pd
import re
from utils import supabase, PRODUCTS_DICT  # Імпортуємо спільні дані


# --- Функції для роботи з даними ---

@st.cache_data(ttl=3600)
def load_data_from_supabase(table_name: str, select_query: str = "*") -> list:
    """
    Універсальна функція для завантаження даних з будь-якої таблиці Supabase.
    УВАГА: Ця функція завантажує лише перші 1000 записів.
    """
    try:
        response = supabase.table(table_name).select(select_query).execute()
        return response.data
    except Exception as e:
        st.error(f"Помилка при завантаженні даних з таблиці '{table_name}': {e}")
        return []


def normalize_address(address: str) -> str:
    """
    Більш надійно очищує і стандартизує рядок адреси.
    Видаляє невидимі символи, зайві пробіли та приводить до нижнього регістру.
    """
    if not isinstance(address, str):
        address = str(address)

    address = address.replace('\xa0', ' ')
    address = re.sub(r'\s+', ' ', address)
    return address.lower().strip()


def get_golden_address(address: str, golden_map: dict) -> dict:
    """
    Шукає адресу у "золотому" словнику. Якщо не знаходить, повертає порожні значення.
    """
    lookup_key = normalize_address(address)
    default_result = {'city': None, 'street': None, 'number': None, 'territory': None}
    return golden_map.get(lookup_key, default_result)


# --- Головна функція для відображення сторінки ---

def show():
    """Відображає сторінку для завантаження та обробки даних."""
    st.title("🚀 Інструмент для завантаження та стандартизації даних")
    st.write(
        "Завантажте ваш Excel-файл. Еталонні дані, регіони та клієнти будуть автоматично завантажені з бази даних Supabase."
    )

    all_regions_data = load_data_from_supabase("region")

    # УВАГА: Якщо у вас > 1000 клієнтів, тут теж може знадобитись повне завантаження
    all_clients_data = load_data_from_supabase("client")
    if all_clients_data:
        client_map = {
            str(row.get("client")).strip(): row.get("new_client")
            for row in all_clients_data
        }
    else:
        st.warning("Не вдалося завантажити довідник клієнтів. Зіставлення не буде виконано.")
        client_map = {}

    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader(
            "1. Виберіть Excel-файл з адресами",
            type=['xlsx', 'xls'],
            key="file_uploader"
        )

    with col2:
        if all_regions_data:
            region_names = [region['name'] for region in all_regions_data]
            selected_region_name = st.selectbox("2. Оберіть регіон для обробки:", region_names, key="region_selector")
        else:
            st.warning("Не вдалося завантажити список регіонів.")
            selected_region_name = None

    if st.button("🚀 Опрацювати", type="primary", key="process_button"):
        if uploaded_file is not None and selected_region_name is not None:
            try:
                df = pd.read_excel(uploaded_file)
                required_columns = ['Регіон', 'Факт.адреса доставки', 'Найменування', 'Клієнт']
                if not all(col in df.columns for col in required_columns):
                    st.error(
                        f"Помилка: В основному файлі відсутня одна з необхідних колонок: {', '.join(required_columns)}.")
                else:
                    df_filtered = df[df['Регіон'] == selected_region_name].copy()
                    if df_filtered.empty:
                        st.warning(f"У файлі не знайдено жодного рядка для регіону '{selected_region_name}'.")
                    else:
                        with st.spinner(f"Завантажуємо 'золоті' адреси для регіону '{selected_region_name}'..."):
                            selected_region_id = next(
                                (r['id'] for r in all_regions_data if r['name'] == selected_region_name), None)
                            if selected_region_id is None:
                                st.error(f"Не вдалося знайти ID для регіону '{selected_region_name}'.")
                                st.stop()

                            all_golden_data = []
                            start_index = 0
                            chunk_size = 1000

                            while True:
                                response = supabase.table("golden_addres").select("*") \
                                    .eq("region_id", selected_region_id) \
                                    .range(start_index, start_index + chunk_size - 1) \
                                    .execute()

                                if not response.data and response.error:
                                    st.error(f"Помилка при завантаженні 'золотих' адрес: {response.error.message}")
                                    st.stop()

                                all_golden_data.extend(response.data)

                                if len(response.data) < chunk_size:
                                    break

                                start_index += chunk_size

                            filtered_golden_data = all_golden_data

                            golden_map = {
                                normalize_address(row.get("Факт.адреса доставки")): {
                                    'city': row.get("Місто"), 'street': row.get("Вулиця"),
                                    'number': str(row.get("Номер будинку")) if row.get(
                                        "Номер будинку") is not None else None,
                                    'territory': row.get("Територія")
                                } for row in filtered_golden_data if row.get("Факт.адреса доставки")
                            }
                        with st.spinner("✨ Зіставляємо адреси та клієнтів..."):
                            parsed_addresses = df_filtered['Факт.адреса доставки'].apply(get_golden_address,
                                                                                         golden_map=golden_map)
                            parsed_df = pd.json_normalize(parsed_addresses)
                            parsed_df = parsed_df.rename(
                                columns={'city': 'City', 'street': 'Street', 'number': 'House_Number',
                                         'territory': 'Territory'})
                            df_filtered.reset_index(drop=True, inplace=True)
                            parsed_df.reset_index(drop=True, inplace=True)
                            df_filtered.drop(columns=['Вулиця', 'Номер будинку', 'Територія', 'Adding'], inplace=True,
                                             errors='ignore')
                            result_df = pd.concat([df_filtered, parsed_df], axis=1)
                            date_match = re.search(r'(\d{4}_\d{2}(_\d{2})?)', uploaded_file.name)
                            result_df['Adding'] = date_match.group(0) if date_match else None
                            if date_match:
                                date_parts = date_match.group(0).split("_")
                                result_df['year'] = date_parts[0]
                                result_df['month'] = date_parts[1]
                                result_df['decade'] = date_parts[2] if len(date_parts) > 2 else None
                            else:
                                result_df['year'] = result_df['month'] = result_df['decade'] = None
                            result_df['Product_Line'] = result_df['Найменування'].str[3:].map(PRODUCTS_DICT)

                            if client_map:
                                result_df['new_client'] = result_df['Клієнт'].astype(str).str.strip().map(client_map)
                            else:
                                result_df['new_client'] = None

                            st.session_state['result_df'] = result_df
            except Exception as e:
                st.error(f"Виникла помилка при обробці файлу: {e}")

    if 'result_df' in st.session_state:
        st.success("Готово! Дані успішно оброблено.")
        result_df = st.session_state['result_df']
        st.dataframe(result_df)
        unmatched_df = result_df[result_df['City'].isna()]
        if not unmatched_df.empty:
            st.subheader("⚠️ Адреси, не знайдені в еталонному списку")
            st.dataframe(unmatched_df[['Факт.адреса доставки']])
        else:
            st.balloons()
            st.success("🎉 Чудово! Всі адреси з обраного регіону були знайдені в еталонному списку.")

        unmatched_clients_df = result_df[result_df['new_client'].isna() & result_df['Клієнт'].notna()]
        if not unmatched_clients_df.empty:
            st.subheader("⚠️ Клієнти, не знайдені в еталонному списку")
            st.dataframe(unmatched_clients_df[['Клієнт']].drop_duplicates())

        ### <<< ЗМІНА: ВІДНОВЛЕНО ЛОГІКУ ЗАВАНТАЖЕННЯ ДАНИХ >>>
        if st.button("💾 Завантажити дані у Supabase", key="upload_button"):
            with st.spinner("Завантаження даних до Supabase..."):
                try:
                    upload_df = result_df.rename(columns={
                        "Дистриб'ютор": "distributor", "Регіон": "region", "Місто": "city_xls",
                        "ЄДРПОУ": "edrpou", "Клієнт": "client", "Юр. адреса клієнта": "client_legal_address",
                        "Факт.адреса доставки": "delivery_address", "Найменування": "product_name",
                        "Кількість": "quantity", "Adding": "adding", "City": "city",
                        "Street": "street", "House_Number": "house_number", "Territory": "territory",
                        "Product_Line": "product_line", "year": "year", "month": "month", "decade": "decade",
                        "new_client": "new_client"
                    })

                    columns_to_upload = [
                        "distributor", "region", "city_xls", "edrpou", "client",
                        "client_legal_address", "delivery_address", "product_name",
                        "quantity", "adding", "city", "street", "house_number",
                        "territory", "product_line", "year", "month", "decade", "new_client"
                    ]

                    final_upload_df = upload_df[[col for col in columns_to_upload if col in upload_df.columns]]
                    # Замінюємо NaN на None, що є еквівалентом NULL в базі даних
                    final_upload_df = final_upload_df.astype(object).where(pd.notna(final_upload_df), None)
                    data_to_insert = final_upload_df.to_dict(orient='records')

                    # Виконуємо вставку даних
                    response = supabase.table("sales_data").insert(data_to_insert).execute()

                    # Перевіряємо відповідь від Supabase
                    if response.data:
                        st.success(f"✅ Дані успішно завантажено. Вставлено {len(response.data)} рядків.")
                    else:
                        # Якщо є помилка, показуємо її
                        st.error(
                            f"Помилка при завантаженні: {response.error.message if response.error else 'Невідома помилка, дані не були вставлені.'}")
                except Exception as e:
                    st.error(f"Сталася критична помилка при підготовці або вставці даних: {e}")
