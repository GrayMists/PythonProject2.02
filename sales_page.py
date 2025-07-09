import streamlit as st
import pandas as pd
from utils import supabase  # Імпортуємо клієнт Supabase з допоміжного файлу


# --- Функції для роботи з даними ---

@st.cache_data(ttl=3600)
def fetch_all_sales_data(territory: str, line: str, months: list) -> pd.DataFrame:
    """
    Завантажує ВСІ дані з таблиці sales_data, використовуючи пагінацію.
    """
    all_data = []
    offset = 0
    page_size = 1000

    select_query = "client, product_name, quantity, city, street, house_number, territory, adding, product_line, delivery_address, year, month, decade"

    while True:
        try:
            query = supabase.table("sales_data").select(select_query).range(offset, offset + page_size - 1)

            if territory != "Всі":
                query = query.eq("territory", territory)
            if line != "Всі":
                query = query.eq("product_line", line)
            if months:  # `months` - це наш список рядків, наприклад ['1', '5']
                query = query.in_("month", months)  # Використовуємо метод .in_()

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

    return pd.DataFrame(all_data)


# --- Головна функція для відображення сторінки ---

def show():
    """Відображає сторінку "Продажі" з відфільтрованими даними та вкладками."""
    st.set_page_config(page_title="Аналіз Продажів", layout="centered")

    st.title("📊 Аналіз продажів")
    st.write(
        "Використовуйте фільтри на бічній панелі, щоб завантажити дані, а потім фільтруйте їх безпосередньо у вкладках.")

    # --- Основна частина сторінки з вкладками ---
    tab1, tab2 = st.tabs(["Загальні продажі", "Деталізація по адресах"])

    # --- ВКЛАДКА 1: Загальні продажі ---
    with tab1:
        st.header("Загальний огляд продажів")

        if 'sales_df_full' in st.session_state and not st.session_state.sales_df_full.empty:
            df_full = st.session_state['sales_df_full']


            # 1. Фільтруємо дані, залишаючи тільки ті, де 'decade' дорівнює 30
            df_decade_30 = df_full[df_full['decade'] == "30"].copy()

            # 2. Перевіряємо, чи є дані після фільтрації
            if df_decade_30.empty:
                st.warning("У завантажених даних немає продажів за '30-ту' декаду.")
            else:
                # Подальший код використовує df_decade_30 замість df_full
                st.markdown("##### Локальні фільтри")
                filter_cols_general = st.columns(2)
                with filter_cols_general[0]:
                    unique_cities = ["Всі"] + sorted(df_decade_30['city'].dropna().unique().tolist())
                    selected_city = st.selectbox("Місто:", unique_cities, key="tab1_city_filter")

                with filter_cols_general[1]:
                    if selected_city != "Всі":
                        streets_in_city = df_decade_30[df_decade_30['city'] == selected_city][
                            'street'].dropna().unique()
                        unique_streets = ["Всі"] + sorted(streets_in_city.tolist())
                    else:
                        unique_streets = ["Всі"] + sorted(df_decade_30['street'].dropna().unique().tolist())
                    selected_street = st.selectbox("Вулиця:", unique_streets, key="tab1_street_filter")

                st.markdown("---")

                df_display = df_decade_30.copy()
                if selected_city != "Всі": df_display = df_display[df_display['city'] == selected_city]
                if selected_street != "Всі": df_display = df_display[df_display['street'] == selected_street]

                st.subheader("Ключові показники")
                kpi1, kpi2, kpi3 = st.columns(3)
                total_quantity = int(pd.to_numeric(df_display['quantity'], errors='coerce').sum())
                unique_clients = df_display['client'].nunique()
                average_quantity = round(pd.to_numeric(df_display['quantity'], errors='coerce').mean(),
                                         2) if not df_display.empty else 0
                kpi1.metric(label="Загальна кількість продажів", value=total_quantity)
                kpi2.metric(label="Кількість унікальних клієнтів", value=unique_clients)
                kpi3.metric(label="Середня кількість в чеку", value=average_quantity)

                st.markdown("---")
                st.subheader("Деталізовані дані")
                st.dataframe(df_display)


        else:
            st.info("Будь ласка, оберіть фільтри на бічній панелі та натисніть 'Отримати дані'.")

    # --- ВКЛАДКА 2: Клієнтські продажі ---
    with tab2:
        st.header("Деталізація по унікальних адресах")

        if 'sales_df_full' in st.session_state and not st.session_state.sales_df_full.empty:
            df_full = st.session_state['sales_df_full']

            st.markdown("##### Локальні фільтри")
            filter_cols_client = st.columns(2)
            with filter_cols_client[0]:
                unique_cities_client = ["Всі"] + sorted(df_full['city'].dropna().unique().tolist())
                selected_city_client = st.selectbox("Місто:", unique_cities_client, key="tab2_city_filter")

            with filter_cols_client[1]:
                if selected_city_client != "Всі":
                    streets_in_city_client = df_full[df_full['city'] == selected_city_client][
                        'street'].dropna().unique()
                    unique_streets_client = ["Всі"] + sorted(streets_in_city_client.tolist())
                else:
                    unique_streets_client = ["Всі"] + sorted(df_full['street'].dropna().unique().tolist())
                selected_street_client = st.selectbox("Вулиця:", unique_streets_client, key="tab2_street_filter")

            st.markdown("---")

            apply_filters_client = st.button("Застосувати", key="tab2_apply_button")

            if apply_filters_client:
                # Фільтруємо дані на основі локальних фільтрів
                df_display_client = df_full.copy()
                if selected_city_client != "Всі":
                    df_display_client = df_display_client[df_display_client['city'] == selected_city_client]
                if selected_street_client != "Всі":
                    df_display_client = df_display_client[df_display_client['street'] == selected_street_client]

                # --- ІНТЕГРОВАНИЙ БЛОК РОЗРАХУНКУ ФАКТИЧНИХ ПРОДАЖІВ ---

                # 1. Створюємо унікальну повну адресу для групування
                df_display_client['full_address_processed'] = (df_display_client['city'].astype(str).fillna('') + ", " + \
                                                               df_display_client['street'].astype(str).fillna(
                                                                   '') + ", " + \
                                                               df_display_client['house_number'].astype(str).fillna(
                                                                   '')).str.strip(' ,')

                # Видаляємо рядки, де адреса не змогла сформуватись
                df_display_client = df_display_client[df_display_client['full_address_processed'] != '']

                # 2. Визначаємо колонки для групування розрахунків
                grouping_cols = ['client', 'product_name', 'full_address_processed', 'year', 'month']

                # 3. Сортуємо дані, щоб декади йшли в правильному порядку
                df_display_client = df_display_client.sort_values(by=grouping_cols + ['decade'])

                # 4. Розраховуємо фактичну кількість, віднімаючи попереднє накопичене значення
                df_display_client['actual_quantity'] = df_display_client.groupby(grouping_cols)['quantity'].diff()

                # 5. Заповнюємо пусті значення (для перших декад) початковими даними
                df_display_client['actual_quantity'] = df_display_client['actual_quantity'].fillna(
                    df_display_client['quantity'])

                # 6. Перетворюємо на ціле число
                df_display_client['actual_quantity'] = df_display_client['actual_quantity'].astype(int)

                # --- КІНЕЦЬ ІНТЕГРОВАНОГО БЛОКУ ---

                # Групуємо вже обраховані дані по адресі для відображення
                grouped = df_display_client.groupby('full_address_processed')

                if grouped.ngroups == 0:
                    st.warning("За обраними фільтрами не знайдено даних.")
                else:
                    st.info(f"Знайдено {grouped.ngroups} унікальних адрес.")

                    for full_address, group in grouped:
                        unique_clients = group['client'].dropna().unique()
                        max_clients = 3
                        clients_preview = ', '.join(unique_clients[:max_clients])
                        suffix = "..." if len(unique_clients) > max_clients else ""
                        expander_title = f"**{full_address}** – {clients_preview}{suffix}"

                        with st.expander(expander_title):
                            # KPI для конкретної адреси (ОНОВЛЕНО)
                            kpi_col1, kpi_col2 = st.columns(2)
                            # Відображаємо суму фактичних продажів у розрізі місяців
                            monthly_sums = group.groupby(['year', 'month'])['actual_quantity'].sum().reset_index()
                            monthly_sums['year_month'] = monthly_sums['year'].astype(str) + '-' + monthly_sums['month'].astype(str).str.zfill(2)
                            # Зменшуємо розмір тексту KPI за допомогою HTML
                            monthly_text_raw = "; ".join([f"{row['year_month']}: {row['actual_quantity']}" for _, row in monthly_sums.iterrows()])
                            monthly_text = f"<span style='font-size: 0.85em'>{monthly_text_raw}</span>"
                            kpi_col1.markdown(f"**Фактичні продажі за адресою (за обрані періоди):**<br>{monthly_text}", unsafe_allow_html=True)


                            # Зведена таблиця з "чистими" продажами (ОНОВЛЕНО)
                            st.subheader("Деталізація по продуктах та періодах (фактичні замволення)")

                            # Перевіряємо, чи є дані для зведеної таблиці
                            if not group.empty:
                                pivot_table = group.pivot_table(
                                    index='product_name',
                                    columns=['year', 'month', 'decade'],
                                    values='actual_quantity',
                                    aggfunc='sum',
                                    fill_value=0
                                )

                                def highlight_positive(val):
                                    return 'background-color: lightgreen' if val > 0 else ''

                                styled_table = pivot_table.style.applymap(highlight_positive)

                                st.dataframe(styled_table)
                            else:
                                st.info("Немає даних для відображення зведеної таблиці.")
            else:
                st.info("Натисніть 'Застосувати', щоб побачити деталізацію.")
        else:
            st.info("Спочатку отримайте дані, використовуючи фільтри на першій вкладці.")

