import streamlit as st
import pandas as pd
import plotly.express as px
from core import data_processing, ui_components, visualizations, data_loader
from datetime import datetime


def show():
    """
    Відображає сторінку "Аналіз продажів".
    """
    st.title("📊 Аналіз продажів")

    if 'sales_df_full' not in st.session_state or st.session_state.sales_df_full.empty:
        st.info("👈 Будь ласка, оберіть фільтри на бічній панелі та натисніть 'Отримати дані'.")
        st.stop()

    df_full = st.session_state.sales_df_full
    df_full = data_processing.create_full_address(df_full.copy())
    address_client_map = data_processing.create_address_client_map(df_full)

    df_latest_decade = pd.DataFrame()
    max_decade = None
    if 'decade' in df_full.columns and not df_full['decade'].dropna().empty:
        available_decades = pd.to_numeric(df_full['decade'], errors='coerce').dropna().unique()
        if len(available_decades) > 0:
            max_decade = int(available_decades.max())
            df_latest_decade = df_full[df_full['decade'] == str(max_decade)].copy()

    tab1, tab2, tab3 = st.tabs(["📈 Загальний огляд", "🏠 Деталізація по адресах", "💰 550"])

    # --- ВКЛАДКА 1: Загальний огляд ---
    with tab1:
        if max_decade is None:
            st.warning("В завантажених даних відсутня інформація про декади для аналізу.")
        else:
            st.header(f"Загальний огляд продажів за останню декаду ({max_decade})")

            if df_latest_decade.empty:
                st.warning(f"Не знайдено даних для {max_decade}-ї декади.")
            else:
                selected_city, selected_street = ui_components.render_local_filters(df_latest_decade, key_prefix="tab1")
                df_display = ui_components.apply_filters(df_latest_decade, selected_city, selected_street)
                kpis = data_processing.calculate_main_kpis(df_display)

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

                visualizations.plot_sales_dynamics(df_display)

                top5_names = kpis['top_products'].index.tolist()
                bottom5_names = kpis['rev_top_products'].index.tolist()
                df_top5 = df_display[df_display['product_name'].isin(top5_names)].copy()
                df_bottom5 = df_display[df_display['product_name'].isin(bottom5_names)].copy()
                visualizations.plot_top_products_bar_chart(df_top5, df_bottom5)

                st.subheader("Зведена таблиця: Міста та Продукти")
                city_product_pivot = df_display.pivot_table(index='city', columns='product_name', values='quantity',
                                                            aggfunc='sum', fill_value=0)
                if not city_product_pivot.empty:
                    city_product_pivot = city_product_pivot.loc[
                        city_product_pivot.sum(axis=1).sort_values(ascending=False).index]

                def highlight_positive_custom(val):
                    return f'background-color: {"#4B6F44" if val > 0 else ""}'

                st.dataframe(city_product_pivot.style.applymap(highlight_positive_custom).format('{:.0f}'))

                with st.expander("Показати теплову карту продажів"):
                    visualizations.plot_city_product_heatmap(city_product_pivot)

    # --- ВКЛАДКА 2: Деталізація по адресах ---
    with tab2:
        st.header("Деталізація фактичних замовлень по унікальних адресах")
        city_client, street_client = ui_components.render_local_filters(df_full, key_prefix="tab2")
        df_display_client = ui_components.apply_filters(df_full, city_client, street_client)

        with st.spinner("Розрахунок фактичних продажів..."):
            df_actual_sales = data_processing.compute_actual_sales(df_display_client)

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

            grouped = df_actual_sales.groupby('full_address')
            st.info(
                f"Знайдено {grouped.ngroups} унікальних адрес з фактичними продажами. Натисніть на адресу, щоб побачити деталі.")

            for full_address, group in grouped:
                client_names = address_client_map.get(full_address, "Невідомий клієнт")
                expander_title = f"**{full_address}** (Клієнти: *{client_names}*)"
                with st.expander(expander_title):
                    st.metric("Всього фактичних продажів за адресою:", f"{group['actual_quantity'].sum():,}")
                    original_rows = df_display_client[df_display_client['full_address'] == full_address]
                    unique_delivery_addresses = original_rows['delivery_address'].dropna().unique()
                    if unique_delivery_addresses.size > 0:
                        st.markdown("**Точки доставки за цією адресою:**")
                        for addr in sorted(unique_delivery_addresses): st.markdown(f"- {addr}")
                    st.markdown("---")
                    st.markdown("**Деталізація по продуктах та періодах (фактичні замовлення)**")
                    pivot_table = group.pivot_table(index='product_name', columns=['year', 'month', 'decade'],
                                                    values='actual_quantity', aggfunc='sum', fill_value=0)
                    st.dataframe(pivot_table.style.applymap(highlight_positive_dark_green).format('{:.0f}'))

    # --- ВКЛАДКА 3: 550 (Аналіз доходу) ---
    with tab3:
        st.header(f"Аналіз доходу ({max_decade if max_decade else 'N/A'})")

        if df_latest_decade.empty:
            st.warning("Немає даних за останню декаду для розрахунку доходу.")
        else:
            months_in_data = df_latest_decade['month'].unique().tolist()

            if not months_in_data:
                st.warning("В даних за останню декаду не знайдено інформації про місяці.")
            else:
                with st.spinner("Завантаження даних про ціни..."):
                    price_df = data_loader.fetch_price_data(months_in_data)

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

                                # --- ОНОВЛЕНИЙ БЛОК: Таблиця з прогнозом по продуктах ---
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
                                        # Сховаємо службові колонки
                                        "daily_quantity_rate": None,
                                        "daily_revenue_rate": None,
                                    },
                                    use_container_width=True,
                                    hide_index=True
                                )
                                # --- Кінець оновленого блоку ---

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


