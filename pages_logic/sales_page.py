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
        # --- ОНОВЛЕНА ЛОГІКА: Динамічний вибір максимальної декади ---
        if 'decade' not in df_full.columns or df_full['decade'].dropna().empty:
            st.warning("В завантажених даних відсутня інформація про декади.")
            st.header("Загальний огляд продажів")
            st.info("Неможливо визначити останню декаду для аналізу.")
        else:
            # Конвертуємо декади в числа, щоб знайти максимум, ігноруючи можливі помилки
            available_decades = pd.to_numeric(df_full['decade'], errors='coerce').dropna().unique()

            if len(available_decades) == 0:
                st.warning("Не вдалося визначити доступні декади в даних.")
            else:
                # Знаходимо максимальну декаду і динамічно оновлюємо заголовок
                max_decade = int(available_decades.max())
                st.header(f"Загальний огляд продажів за останню декаду ({max_decade})")

                # 1. Фільтруємо дані для цієї вкладки по максимальній декаді
                df_latest_decade = df_full[df_full['decade'] == str(max_decade)].copy()

                if df_latest_decade.empty:
                    st.warning(f"Не знайдено даних для {max_decade}-ї декади.")
                else:
                    # 2. Відображаємо та застосовуємо локальні фільтри
                    selected_city, selected_street = ui_components.render_local_filters(df_latest_decade,
                                                                                        key_prefix="tab1")
                    df_display = ui_components.apply_filters(df_latest_decade, selected_city, selected_street)

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

                    top5_names = kpis['top_products'].index.tolist()
                    bottom5_names = kpis['rev_top_products'].index.tolist()

                    df_top5 = df_display[df_display['product_name'].isin(top5_names)].copy()
                    df_bottom5 = df_display[df_display['product_name'].isin(bottom5_names)].copy()

                    visualizations.plot_top_products_bar_chart(df_top5, df_bottom5)

                    # 6. Додаємо зведену таблицю та теплову карту
                    st.subheader("Зведена таблиця: Міста та Продукти")

                    city_product_pivot = df_display.pivot_table(
                        index='city',
                        columns='product_name',
                        values='quantity',
                        aggfunc='sum',
                        fill_value=0
                    )

                    if not city_product_pivot.empty:
                        city_product_pivot = city_product_pivot.loc[
                            city_product_pivot.sum(axis=1).sort_values(ascending=False).index]

                    def highlight_positive_custom(val):
                        if val > 0:
                            return 'background-color: #5c765e; color: white;'
                        else:
                            return ''

                    city_product_pivot.index.name = "Місто"
                    st.dataframe(city_product_pivot.style.applymap(highlight_positive_custom).format('{:.0f}'))

                    with st.expander("Показати теплову карту продажів"):
                        visualizations.plot_city_product_heatmap(city_product_pivot)

    # --- ВКЛАДКА 2: Деталізація по адресах ---
    with tab2:
        st.header("Деталізація фактичних замовлень по клієнтах та адресах")

        # 1. Фільтри та розрахунок продажів (без змін)
        city_client, street_client = ui_components.render_local_filters(df_full, key_prefix="tab2")
        df_display_client = ui_components.apply_filters(df_full, city_client, street_client)

        with st.spinner("Розрахунок фактичних продажів..."):
            df_actual_sales = data_processing.compute_actual_sales(df_display_client)

        if 'new_client' not in df_actual_sales.columns:
            st.error("Помилка: у даних відсутня колонка 'new_client'. Оновіть запит до бази даних.")
        elif df_actual_sales.empty:
            st.warning("За обраними фільтрами не знайдено даних для розрахунку.")
        else:
            def highlight_positive_dark_green(val):
                return 'background-color: #5c765e; color: white;' if val > 0 else ''

            # Загальна зведена таблиця (без змін)
            st.subheader("Загальна зведена таблиця по фактичних продажах")
            summary_pivot_table = df_actual_sales.pivot_table(
                index='product_name',
                columns=['year', 'month', 'decade'],
                values='actual_quantity',
                aggfunc='sum', fill_value=0
            )
            summary_pivot_table.index.name = "Препарати"
            st.dataframe(summary_pivot_table.style.applymap(highlight_positive_dark_green).format('{:.0f}'))
            st.markdown("---")

            ### --- ОСНОВНА ЗМІНА ЛОГІКИ ТУТ --- ###

            # 1. Групуємо одразу за парою "клієнт-адреса"
            grouped = df_actual_sales.groupby(['new_client', 'full_address'])

            st.info(f"Знайдено **{grouped.ngroups}** унікальних пар 'клієнт-адреса' з фактичними продажами.")

            # 2. Ітеруємо по згрупованих даних
            for (client_name, full_address), group in grouped:

                # 3. Формуємо єдиний заголовок для експандера
                expander_title = f"**{client_name}** | 📍 {full_address}"

                with st.expander(expander_title):
                    total_actual_quantity = group['actual_quantity'].sum()
                    st.metric("Всього фактичних продажів:", f"{total_actual_quantity:,.0f}")

                    st.markdown("**Точки доставки за цією адресою:**")
                    original_rows = df_display_client[
                        (df_display_client['full_address'] == full_address) &
                        (df_display_client['new_client'] == client_name)
                        ]
                    unique_delivery_addresses = original_rows['delivery_address'].dropna().unique()

                    if len(unique_delivery_addresses) > 0:
                        for addr in sorted(unique_delivery_addresses):
                            st.markdown(f"- {addr}")
                    else:
                        st.markdown("- *Адреси доставки не вказано*")

                    st.markdown("---")

                    st.markdown("**Деталізація по продуктах та періодах:**")
                    pivot_table = group.pivot_table(
                        index='product_name',
                        columns=['year', 'month', 'decade'],
                        values='actual_quantity',
                        aggfunc='sum', fill_value=0
                    )
                    pivot_table.index.name = "Препарати"
                    st.dataframe(pivot_table.style.applymap(highlight_positive_dark_green).format('{:.0f}'))
