import streamlit as st
import pandas as pd
import plotly.express as px
from core import data_processing, ui_components, visualizations, data_loader


def show():
    """
    Відображає сторінку "Аналіз продажів".
    """
    st.title("📊 Аналіз продажів")

    if 'sales_df_full' not in st.session_state or st.session_state.sales_df_full.empty:
        st.info("👈 Будь ласка, оберіть фільтри на бічній панелі та натисніть 'Отримати дані'.")
        st.stop()

    if 'selected_region_id' not in st.session_state or not st.session_state.get('selected_region_id'):
        st.error("Помилка: ID регіону не знайдено в поточній сесії.")
        st.info(
            "Будь ласка, поверніться до панелі управління, оберіть фільтри та натисніть 'Отримати дані' ще раз.")
        st.stop()

    df_full = st.session_state.sales_df_full
    df_full = data_processing.create_full_address(df_full.copy())
    address_client_map = data_processing.create_address_client_map(df_full)

    # Ensure 'year', 'month', 'decade' are numeric for consistent processing
    df_full['year'] = pd.to_numeric(df_full['year'], errors='coerce')
    df_full['month'] = pd.to_numeric(df_full['month'], errors='coerce')
    df_full['decade'] = pd.to_numeric(df_full['decade'], errors='coerce')

    df_full_with_revenue = df_full.copy()
    all_months_in_data = df_full_with_revenue['month'].dropna().unique().tolist()
    region_id_to_load = st.session_state.get('selected_region_id')

    if all_months_in_data and region_id_to_load:
        price_df_full = data_loader.fetch_price_data(
            region_id=region_id_to_load,
            months=[f"{int(m):02d}" for m in all_months_in_data]
        )
        if not price_df_full.empty:
            df_full_with_revenue['month'] = df_full_with_revenue['month'].astype('Int64')
            df_full_with_revenue = pd.merge(df_full_with_revenue, price_df_full, on=['product_name', 'month'],
                                            how='left')
            df_full_with_revenue['revenue'] = df_full_with_revenue['quantity'] * df_full_with_revenue['price']

    max_decade_per_month = df_full.groupby(['year', 'month'])['decade'].transform('max')
    is_latest_for_month = (df_full['decade'] == max_decade_per_month)
    df_for_overview = df_full[is_latest_for_month].copy()

    df_latest_decade = pd.DataFrame()
    max_decade = None
    if not df_for_overview.empty and 'decade' in df_for_overview.columns:
        max_decade = int(df_for_overview['decade'].max())
        df_latest_decade = df_for_overview[df_for_overview['decade'] == max_decade].copy()

    tab1, tab2, tab3 = st.tabs(["📈 Загальний огляд", "🏠 Деталізація по адресах", "💰 550"])

    with tab1:
        st.header("Загальний огляд продажів за обраний період")
        selected_city, selected_street = ui_components.render_local_filters(df_for_overview, key_prefix="tab1")
        df_display = ui_components.apply_filters(df_for_overview, selected_city, selected_street)
        df_for_dynamics = ui_components.apply_filters(df_full_with_revenue, selected_city, selected_street)

        if df_display.empty:
            st.warning("За обраними фільтрами дані відсутні.")
        else:
            st.markdown("""
                <style>
                [data-testid="stMetricValue"] {
                    font-size: 18px;
                }
                [data-testid="stMetricLabel"] {
                    font-size: 16px;
                    font-weight: bold;
                }
                </style>
            """, unsafe_allow_html=True)
            kpis = data_processing.calculate_main_kpis(df_display)
            st.subheader("Ключові показники")
            kpi_cols = st.columns(5)
            kpi_cols[0].metric("Загальна кількість", f"{kpis['total_quantity']:,}")
            kpi_cols[1].metric("Унікальні продукти", f"{kpis['unique_products']:,}")
            kpi_cols[2].metric("Унікальні клієнти", f"{kpis['unique_clients']:,}")
            kpi_cols[3].metric("Частка ТОП-5 (%)", f"{kpis['top5_share']:.1f}%")
            total_revenue = df_for_dynamics['revenue'].sum() if 'revenue' in df_for_dynamics.columns else 0
            kpi_cols[4].metric("Загальний дохід", f"{total_revenue:,.2f} грн")

            visualizations.plot_sales_dynamics(df_for_dynamics)
            visualizations.plot_top_products_summary(df_display)

            st.subheader("Зведена таблиця: Міста та Продукти")
            city_product_pivot = df_display.pivot_table(index='city', columns='product_name', values='quantity',
                                                        aggfunc='sum', fill_value=0)
            if not city_product_pivot.empty:
                city_product_pivot = city_product_pivot.loc[
                    city_product_pivot.sum(axis=1).sort_values(ascending=False).index]
                st.dataframe(city_product_pivot.style.applymap(
                    lambda val: 'background-color: #4B6F44' if val > 0 else '').format('{:.0f}'))
                with st.expander("Показати теплову карту продажів"):
                    visualizations.plot_city_product_heatmap(city_product_pivot)

    with tab2:
        st.header("Деталізація фактичних замовлень по унікальних адресах")
        city_client, street_client = ui_components.render_local_filters(df_full, key_prefix="tab2")
        df_display_client_filtered = ui_components.apply_filters(df_full, city_client, street_client)

        with st.spinner("Розрахунок фактичних продажів..."):
            if not df_display_client_filtered.empty:
                df_actual_sales = data_processing.compute_actual_sales(df_display_client_filtered.copy())
                # --- Додано для відладки: вивід df_actual_sales ---
                st.subheader("DEBUG: Результат compute_actual_sales")
                st.dataframe(df_actual_sales)
                # --- Кінець секції відладки ---
            else:
                df_actual_sales = pd.DataFrame()

        if df_actual_sales.empty:
            st.warning("За обраними фільтрами не знайдено даних для розрахунку.")
        else:
            def highlight_positive_dark_green(val):
                return f'background-color: {"#4B6F44" if val > 0 else ""}'

            st.subheader("Загальна зведена таблиця по фактичних продажах")
            summary_pivot_table = df_actual_sales.pivot_table(index='product_name', columns=['year', 'month', 'decade'],
                                                              values='actual_quantity', aggfunc='sum', fill_value=0)
            st.dataframe(summary_pivot_table.style.applymap(highlight_positive_dark_green).format('{:.0f}'))
            st.markdown("---")

            grouped = df_actual_sales.groupby(['full_address', 'new_client'])
            st.info(f"Знайдено {grouped.ngroups} унікальних комбінацій адрес і клієнтів з фактичними продажами.")

            for (full_address, client_name), group in grouped:
                expander_title = f"**{full_address}** (Клієнт: *{client_name}*)"
                with st.expander(expander_title):
                    st.metric("Всього фактичних продажів за адресою:", f"{group['actual_quantity'].sum():,}")
                    pivot_table = group.pivot_table(index='product_name', columns=['year', 'month', 'decade'],
                                                    values='actual_quantity', aggfunc='sum', fill_value=0)
                    st.dataframe(pivot_table.style.applymap(highlight_positive_dark_green).format('{:.0f}'))

    with tab3:
        st.header(f"Аналіз доходу за останню декаду ({max_decade if max_decade else 'N/A'})")

        if df_latest_decade.empty:
            st.warning("Немає даних за останню декаду для розрахунку доходу.")
        else:
            months_in_data = df_latest_decade['month'].unique().tolist()

            if not months_in_data:
                st.warning("В даних за останню декаду не знайдено інформації про місяці.")
            else:
                with st.spinner("Завантаження даних про ціни..."):
                    region_id_to_load = st.session_state.selected_region_id
                    price_df = data_loader.fetch_price_data(
                        region_id=region_id_to_load,
                        months=months_in_data
                    )

                if price_df.empty:
                    st.error("Не вдалося завантажити дані про ціни для обраних місяців. Розрахунок доходу неможливий.")
                else:
                    sales_df_for_merge = df_latest_decade.copy()
                    sales_df_for_merge['month'] = pd.to_numeric(sales_df_for_merge['month'], errors='coerce').astype(
                        'Int64')
                    merged_df = pd.merge(sales_df_for_merge, price_df, on=['product_name', 'month'], how='left')
                    products_no_price = merged_df[merged_df['price'].isnull()]['product_name'].unique()

                    if products_no_price.size > 0:
                        with st.expander("⚠️ Увага: Не для всіх продуктів знайдено ціну"):
                            st.write("Для наступних продуктів не знайдено ціну за відповідний місяць:")
                            for prod in products_no_price: st.markdown(f"- {prod}")

                    merged_df['revenue'] = merged_df['quantity'] * merged_df['price']
                    final_df = merged_df.dropna(subset=['revenue'])

                    if final_df.empty:
                        st.warning("Після об'єднання з цінами не залишилось даних для аналізу доходу.")
                    else:
                        total_revenue = final_df['revenue'].sum()
                        total_quantity_sold = final_df['quantity'].sum()

                        st.subheader("Ключові показники доходу")
                        kpi_cols = st.columns(2)
                        kpi_cols[0].metric("Загальний дохід (факт)", f"{total_revenue:,.2f} грн")
                        kpi_cols[1].metric("Загальна кількість (факт)", f"{total_quantity_sold:,.0f}")

                        st.markdown("---")
                        st.markdown("##### Деталізація доходу по продуктах (факт)")
                        revenue_summary = final_df.groupby('product_name').agg(
                            total_quantity=('quantity', 'sum'),
                            total_revenue=('revenue', 'sum')
                        ).sort_values(by='total_revenue', ascending=False)

                        top5_revenue = revenue_summary.head(5)
                        bottom5_revenue = revenue_summary.tail(5)

                        st.subheader("ТОП-5 продуктів за доходом")
                        top5_col, bottom5_col = st.columns(2)

                        with top5_col:
                            st.markdown("**Найуспішніші продукти**")
                            st.dataframe(
                                top5_revenue,
                                column_config={
                                    "total_quantity": st.column_config.NumberColumn("К-сть", format="%d"),
                                    "total_revenue": st.column_config.NumberColumn("Сума", format="%.2f грн")
                                },
                                use_container_width=True
                            )

                        with bottom5_col:
                            st.markdown("**Продукти з найменшим доходом**")
                            st.dataframe(
                                bottom5_revenue,
                                column_config={
                                    "total_quantity": st.column_config.NumberColumn("К-сть", format="%d"),
                                    "total_revenue": st.column_config.NumberColumn("Сума", format="%.2f грн")
                                },
                                use_container_width=True
                            )

                        st.dataframe(
                            revenue_summary.style.format({
                                'total_quantity': '{:,.0f}',
                                'total_revenue': '{:,.2f} грн'
                            }).background_gradient(cmap='Greens', subset=['total_revenue']),
                            use_container_width=True
                        )

                        if max_decade < 30:
                            st.markdown("---")
                            st.subheader("📈 Прогноз до кінця місяця")

                            with st.spinner("Виконуємо симуляції для прогнозу..."):
                                forecast_data = data_processing.calculate_forecast_with_bootstrap(
                                    df_for_current_month=final_df,
                                    last_decade=max_decade,
                                    year=int(df_latest_decade['year'].iloc[0]),
                                    month=int(df_latest_decade['month'].iloc[0])
                                )

                            if forecast_data:
                                forecast_cols = st.columns(2)
                                forecast_cols[0].metric(
                                    label="Прогноз доходу (точковий)",
                                    value=f"{forecast_data['point_forecast_revenue']:,.2f} грн"
                                )
                                forecast_cols[1].metric(
                                    label="95% Довірчий інтервал (дохід)",
                                    value=f"{forecast_data['conf_interval_revenue'][0]:,.0f} - {forecast_data['conf_interval_revenue'][1]:,.0f} грн",
                                    help="З 95% ймовірністю, фінальний дохід буде в цьому діапазоні."
                                )

                                st.markdown("##### Деталізація прогнозу по продуктах")
                                product_forecast_df = data_processing.calculate_product_level_forecast(
                                    df_for_current_month=final_df,
                                    workdays_passed=forecast_data['workdays_passed'],
                                    workdays_left=forecast_data['workdays_left']
                                )
                                st.dataframe(
                                    product_forecast_df,
                                    column_config={
                                        "product_name": st.column_config.TextColumn("Продукт"),
                                        "quantity_so_far": st.column_config.NumberColumn("Факт (к-сть)",
                                                                                         format="%d уп."),
                                        "forecast_quantity": st.column_config.NumberColumn("Прогноз (к-сть)",
                                                                                           format="%.1f уп."),
                                        "revenue_so_far": st.column_config.NumberColumn("Факт (дохід)",
                                                                                        format="%.2f грн"),
                                        "forecast_revenue": st.column_config.NumberColumn("Прогноз (дохід)",
                                                                                          format="%.2f грн"),
                                        "daily_quantity_rate": None,
                                        "daily_revenue_rate": None,
                                    },
                                    use_container_width=True,
                                    hide_index=True
                                )

                                with st.expander("Деталі методології та розподіл (Bootstrap)"):
                                    st.info(
                                        "Цей прогноз базується на симуляції 1000 можливих варіантів майбутнього на основі "
                                        "поточних темпів продажів. Гістограма нижче показує розподіл цих симуляцій."
                                    )
                                    fig = px.histogram(
                                        x=forecast_data['bootstrap_distribution_revenue'],
                                        nbins=50,
                                        labels={'x': 'Прогнозований дохід'},
                                        title="Розподіл результатів симуляцій"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
