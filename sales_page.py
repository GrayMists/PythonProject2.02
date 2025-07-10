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

            # Створюємо колонку адреси у df_full (як у df_display_client)
            df_full['full_address_processed'] = (
                df_full['city'].astype(str).fillna('') + ", " +
                df_full['street'].astype(str).fillna('') + ", " +
                df_full['house_number'].astype(str).fillna('')
            ).str.strip(' ,')


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
                total_quantity = int(pd.to_numeric(df_display['quantity'], errors='coerce').sum())
                top_products = df_display.groupby('product_name')['quantity'].sum().sort_values(ascending=False).head(5)
                rev_top_products = df_display.groupby('product_name')['quantity'].sum().sort_values(ascending=True).head(5)
                # Розрахунок нових метрик
                unique_products = df_display['product_name'].nunique()
                # Формуємо об'єднану адресу
                df_display['full_address'] = (
                    df_display['city'].astype(str).fillna('') + ", " +
                    df_display['street'].astype(str).fillna('') + ", " +
                    df_display['house_number'].astype(str).fillna('')
                ).str.strip(', ')
                unique_clients = df_display['full_address'].nunique()
                avg_quantity_per_client = total_quantity / unique_clients if unique_clients else 0
                # Додана метрика: частка ТОП-5 продуктів у загальному обсязі
                top5_total = top_products.sum()
                top5_share = top5_total / total_quantity * 100 if total_quantity else 0
                # KPI-картки в два ряди по 3 колонки
                kpi_row1 = st.columns(3)
                kpi_row2 = st.columns(3)

                with kpi_row1[0]:
                    st.markdown(f"""
                        <div style="height: 140px; margin: 10px; padding: 1rem; border-radius: 10px; background-color: #f4f4f4; text-align: center; border: 1px solid #ddd; display: flex; flex-direction: column; justify-content: center;">
                            <div style="font-size: 14px; color: #555;">Загальна кількість проданих упаковок</div>
                            <div style="font-size: 32px; font-weight: bold; color: #f45b00;">{total_quantity:,}</div>
                        </div>
                    """, unsafe_allow_html=True)

                with kpi_row1[1]:
                    st.markdown(f"""
                        <div style="height: 140px; margin: 10px; padding: 1rem; border-radius: 10px; background-color: #f4f4f4; text-align: center; border: 1px solid #ddd; display: flex; flex-direction: column; justify-content: center;">
                            <div style="font-size: 14px; color: #555;">Унікальні продукти</div>
                            <div style="font-size: 28px; font-weight: bold; color: #3366cc;">{unique_products}</div>
                        </div>
                    """, unsafe_allow_html=True)

                with kpi_row1[2]:
                    st.markdown(f"""
                        <div style="height: 140px; margin: 10px; padding: 1rem; border-radius: 10px; background-color: #f4f4f4; text-align: center; border: 1px solid #ddd; display: flex; flex-direction: column; justify-content: center;">
                            <div style="font-size: 14px; color: #555;">Унікальні клієнти</div>
                            <div style="font-size: 28px; font-weight: bold; color: #3366cc;">{unique_clients}</div>
                        </div>
                    """, unsafe_allow_html=True)

                with kpi_row2[0]:
                    st.markdown(f"""
                        <div style="height: 140px; margin: 10px; padding: 1rem; border-radius: 10px; background-color: #f4f4f4; text-align: center; border: 1px solid #ddd; display: flex; flex-direction: column; justify-content: center;">
                            <div style="font-size: 14px; color: #555;">Середня кількість на клієнта</div>
                            <div style="font-size: 28px; font-weight: bold; color: #3366cc;">{avg_quantity_per_client:.1f}</div>
                        </div>
                    """, unsafe_allow_html=True)

                with kpi_row2[1]:
                    st.markdown(f"""
                        <div style="height: 140px; margin: 10px; padding: 1rem; border-radius: 10px; background-color: #f4f4f4; text-align: center; border: 1px solid #ddd; display: flex; flex-direction: column; justify-content: center;">
                            <div style="font-size: 14px; color: #555;">Частка ТОП-5 продуктів у загальному обсязі (%)</div>
                            <div style="font-size: 28px; font-weight: bold; color: #3366cc;">{top5_share:.1f}%</div>
                        </div>
                    """, unsafe_allow_html=True)

                with kpi_row2[2]:
                    # Можна залишити порожнім або додати іншу метрику в майбутньому
                    st.markdown("")

                # Таблиці ТОП-5 винесені в окремий рядок з двома колонками
                kpi_row3 = st.columns(2)

                with kpi_row3[0]:
                    st.markdown("**ТОП-5 найбільш продаваних продуктів:**")
                    st.dataframe(top_products.reset_index().rename(columns={'quantity': 'Кількість'}), hide_index=True)

                with kpi_row3[1]:
                    st.markdown("**ТОП-5 найменш продаваних продуктів:**")
                    st.dataframe(rev_top_products.reset_index().rename(columns={'quantity': 'Кількість'}), hide_index=True)

                st.markdown("---")
                st.subheader("Деталізовані дані")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Зведена таблиця: Міста**")
                    st.dataframe(
                        df_display.groupby('city', as_index=False)['quantity']
                        .sum()
                        .sort_values(by='quantity', ascending=False)
                        .rename(columns={'city': 'Місто', 'quantity': 'Кількість'}),
                        hide_index=True
                    )
                with col2:
                    st.markdown("**Зведена таблиця: Вулиці та Продукти**")
                    st.dataframe(
                        df_display.groupby('street', as_index=False)['quantity']
                        .sum()
                        .sort_values(by='quantity', ascending=False)
                        .rename(columns={'street': 'Вулиця', 'quantity': 'Кількість'}),
                        hide_index=True
                    )
                st.markdown("**Зведена таблиця: Продукти**")
                st.dataframe(
                    df_display.groupby('product_name', as_index=False)['quantity']
                        .sum()
                        .sort_values(by='quantity', ascending=False)
                        .rename(columns={'product_name': 'Продукт', 'quantity': 'Кількість'}),
                    hide_index=True
                )

                # --- Додаємо зведену таблицю по місту × продукту ---
                st.subheader("Зведена таблиця: Міста та Продукти")
                city_product_pivot = df_display.pivot_table(
                    index='city',
                    columns='product_name',
                    values='quantity',
                    aggfunc='sum',
                    fill_value=0
                )

                def highlight_positive(val):
                    return 'background-color: #355E3B' if val > 0 else ''

                st.dataframe(city_product_pivot.style.applymap(highlight_positive))



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

                # --- Створюємо мапу адреса → клієнти для відображення у заголовках ---
                address_clients_map = (
                    df_full.groupby('full_address_processed')['client']
                    .unique()
                    .apply(lambda x: ', '.join(sorted(x[:3])) + ('...' if len(x) > 3 else ''))
                    .to_dict()
                )

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

                # 4-6. Коректний розрахунок фактичної кількості між декадами
                def compute_actual(group):
                    # Агрегуємо кількість по унікальних декадах, щоб уникнути дублювання
                    group_agg = group.groupby(['product_name', 'full_address_processed', 'year', 'month', 'decade'])['quantity'].sum().reset_index()

                    pivot = group_agg.pivot(index=['product_name', 'full_address_processed', 'year', 'month'],
                                            columns='decade',
                                            values='quantity').fillna(0)

                    pivot['fact_30'] = pivot.get('30', 0) - (pivot.get('20', 0) if '20' in pivot else pivot.get('10', 0))
                    pivot['fact_20'] = pivot.get('20', 0) - pivot.get('10', 0)
                    pivot['fact_10'] = pivot.get('10', 0)

                    result = pivot[['fact_10', 'fact_20', 'fact_30']].stack().reset_index()
                    result.columns = ['product_name', 'full_address_processed', 'year', 'month', 'decade', 'actual_quantity']
                    result['decade'] = result['decade'].str.replace('fact_', '')
                    return result

                grouped_actual = df_display_client.groupby(['product_name', 'full_address_processed', 'year', 'month'])
                df_display_client = grouped_actual.apply(compute_actual).reset_index(drop=True)

                # --- КІНЕЦЬ ІНТЕГРОВАНОГО БЛОКУ ---

                # Групуємо вже обраховані дані по адресі для відображення
                grouped = df_display_client.groupby('full_address_processed')

                if grouped.ngroups == 0:
                    st.warning("За обраними фільтрами не знайдено даних.")
                else:
                    st.info(f"Знайдено {grouped.ngroups} унікальних адрес.")

                    for full_address, group in grouped:
                        client_names = address_clients_map.get(full_address, "")
                        expander_title = f"**{full_address}** – {client_names}"

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
                                    return 'background-color: #355E3B' if val > 0 else ''

                                styled_table = pivot_table.style.applymap(highlight_positive)

                                st.dataframe(styled_table)
                            else:
                                st.info("Немає даних для відображення зведеної таблиці.")
            else:
                st.info("Натисніть 'Застосувати', щоб побачити деталізацію.")
        else:
            st.info("Спочатку отримайте дані, використовуючи фільтри на першій вкладці.")
