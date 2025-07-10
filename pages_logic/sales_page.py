import streamlit as st
import pandas as pd
from core import data_processing, ui_components, visualizations


def show():
    """
    Відображає сторінку "Аналіз продажів".
    Ця функція тепер відповідає тільки за компонування елементів на сторінці.
    """
    st.title("📊 Аналіз продажів")

    # Перевіряємо, чи дані були завантажені в home.py
    if 'sales_df_full' not in st.session_state or st.session_state.sales_df_full.empty:
        st.info("👈 Будь ласка, оберіть фільтри на бічній панелі та натисніть 'Отримати дані'.")
        st.stop()

    # Отримуємо дані з сесії
    df_full = st.session_state.sales_df_full
    # Одноразово створюємо колонку з повною адресою
    df_full = data_processing.create_full_address(df_full.copy())
    # Створюємо словник "адреса -> клієнти" для використання у заголовках
    address_client_map = data_processing.create_address_client_map(df_full)

    tab1, tab2 = st.tabs(["📈 Загальний огляд", "🏠 Деталізація по адресах"])

    # --- ВКЛАДКА 1: Загальний огляд ---
    with tab1:
        st.header("Загальний огляд продажів за 30-ту декаду")

        # 1. Фільтруємо дані для цієї вкладки
        df_decade_30 = df_full[df_full['decade'] == "30"].copy()
        if df_decade_30.empty:
            st.warning("У завантажених даних немає продажів за '30-ту' декаду.")
        else:
            # 2. Відображаємо та застосовуємо локальні фільтри
            selected_city, selected_street = ui_components.render_local_filters(df_decade_30, key_prefix="tab1")
            df_display = ui_components.apply_filters(df_decade_30, selected_city, selected_street)

            # 3. Розраховуємо KPI
            kpis = data_processing.calculate_main_kpis(df_display)

            # 4. Відображаємо KPI
            st.subheader("Ключові показники")
            kpi_cols = st.columns(4)
            with kpi_cols[0]:
                ui_components.display_kpi_card("Загальна кількість", f"{kpis['total_quantity']:,}")
            with kpi_cols[1]:
                ui_components.display_kpi_card("Унікальні продукти", f"{kpis['unique_products']:,}")
            with kpi_cols[2]:
                ui_components.display_kpi_card("Унікальні клієнти", f"{kpis['unique_clients']:,}")
            with kpi_cols[3]:
                ui_components.display_kpi_card("Частка ТОП-5 (%)", f"{kpis['top5_share']:.1f}%")

            st.markdown("---")

            # 5. Відображаємо візуалізації
            visualizations.plot_sales_dynamics(df_display)
            visualizations.plot_top_products_bar_chart(kpis['top_products'], kpis['rev_top_products'])

            # 6. Додаємо зведену таблицю та теплову карту
            st.subheader("Зведена таблиця: Міста та Продукти")
            df_display = df_display.rename(columns={'city': 'Місто'})

            city_product_pivot = df_display.pivot_table(
                index='Місто',
                columns='product_name',
                values='quantity',
                aggfunc='sum',
                fill_value=0
            )
            city_product_pivot = city_product_pivot.loc[city_product_pivot.sum(axis=1).sort_values(ascending=False).index]

            # Функція для підсвічування всіх позитивних значень вказаним кольором
            def highlight_positive_custom(val):
                color = '#4B6F44' if val > 0 else ''  # Темно-зелений для позитивних значень
                return f'background-color: {color}'

            st.dataframe(city_product_pivot.style.applymap(highlight_positive_custom).format('{:.0f}'))

            with st.expander("Показати теплову карту продажів"):
                visualizations.plot_city_product_heatmap(df_display)

    # --- ВКЛАДКА 2: Деталізація по адресах ---
    with tab2:
        st.header("Деталізація фактичних замовлень по унікальних адресах")

        # 1. Локальні фільтри для цієї вкладки
        city_client, street_client = ui_components.render_local_filters(df_full, key_prefix="tab2")
        df_display_client = ui_components.apply_filters(df_full, city_client, street_client)

        # 2. Розраховуємо "чисті" продажі
        with st.spinner("Розрахунок фактичних продажів..."):
            df_actual_sales = data_processing.compute_actual_sales(df_display_client)

        if df_actual_sales.empty:
            st.warning("За обраними фільтрами не знайдено даних для розрахунку.")
        else:
            # 3. Групуємо по адресі для відображення в експандерах
            grouped = df_actual_sales.groupby('full_address')
            st.info(f"Знайдено {grouped.ngroups} унікальних адрес з фактичними продажами.")

            for full_address, group in grouped:
                # Отримуємо імена клієнтів зі словника
                client_names = address_client_map.get(full_address, "Невідомий клієнт")
                expander_title = f"**{full_address}** (Клієнти: *{client_names}*)"

                with st.expander(expander_title):
                    total_actual_quantity = group['actual_quantity'].sum()
                    st.metric("Всього фактичних продажів за адресою:", f"{total_actual_quantity:,}")

                    # Відображаємо унікальні адреси доставки
                    st.markdown("**Точки доставки за цією адресою:**")
                    original_rows = df_display_client[df_display_client['full_address'] == full_address]
                    unique_delivery_addresses = original_rows['delivery_address'].dropna().unique()

                    if len(unique_delivery_addresses) > 0:
                        for addr in sorted(unique_delivery_addresses):
                            st.markdown(f"- {addr}")
                    else:
                        st.markdown("- *Адреси доставки не вказано*")

                    st.markdown("---")

                    # Зведена таблиця з "чистими" продажами
                    st.markdown("**Деталізація по продуктах та періодах (фактичні замовлення)**")
                    pivot_table = group.pivot_table(
                        index='product_name',
                        columns=['year', 'month', 'decade'],
                        values='actual_quantity',
                        aggfunc='sum',
                        fill_value=0
                    )

                    # Функція для підсвічування всіх позитивних значень
                    def highlight_positive(val):
                        color = '#a8d08d' if val > 0 else ''  # Світло-зелений для позитивних значень
                        return f'background-color: {color}'

                    st.dataframe(pivot_table.style.applymap(highlight_positive).format('{:.0f}'))
