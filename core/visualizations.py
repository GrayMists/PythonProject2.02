import streamlit as st
import pandas as pd
import plotly.express as px


# Словник для перекладу номерів місяців у назви українською
UKRAINIAN_MONTHS = {
    1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень",
    5: "Травень", 6: "Червень", 7: "Липень", 8: "Серпень",
    9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень"
}


def plot_top_products_summary(df: pd.DataFrame):
    """
    Створює зведену таблицю по всіх продуктах та стовпчасту діаграму для ТОП-5.
    """
    if df.empty:
        st.info("Немає даних для побудови зведення по продуктах.")
        return

    product_summary = df.groupby('product_name')['quantity'].sum().sort_values(ascending=False).reset_index()
    product_summary.rename(columns={'quantity': 'Загальна кількість'}, inplace=True)
    top5_products = product_summary.head(5)

    df_top5_details = df[df['product_name'].isin(top5_products['product_name'])].copy()
    df_top5_details['month_name'] = pd.to_numeric(df_top5_details['month']).map(UKRAINIAN_MONTHS)
    df_top5_agg = df_top5_details.groupby(['product_name', 'month_name'])['quantity'].sum().reset_index()

    st.markdown("---")
    st.subheader("Аналіз продажів за продуктами")
    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown("**Загальні продажі**")
        st.dataframe(
            product_summary,
            column_config={"product_name": "Продукт",
                           "Загальна кількість": st.column_config.NumberColumn("К-сть", format="%d")},
            use_container_width=True, hide_index=True
        )

    with col2:
        st.markdown("**ТОП-5 найбільш продаваних**")
        top_order = top5_products.sort_values(by='Загальна кількість', ascending=True)['product_name']
        fig_top = px.bar(
            df_top5_agg, y='product_name', x='quantity', orientation='h',
            labels={'quantity': 'Кількість', 'product_name': 'Продукт', 'month_name': 'Місяць'},
            category_orders={'product_name': top_order},
            color_discrete_sequence=['#00656e']
        )
        fig_top.update_traces(textfont_color='black')
        totals_top = df_top5_agg.groupby('product_name')['quantity'].sum()
        for product in top_order:
            total_val = totals_top.get(product, 0)
            fig_top.add_annotation(
                y=product, x=total_val, text=f"<b>{total_val}</b>", showarrow=False,
                xanchor='left', xshift=5, font=dict(color="black")
            )
        fig_top.update_layout(
            title_text="Найбільш продавані", title_x=0.5, yaxis_title=None, xaxis_title=None,
            uniformtext_minsize=8, uniformtext_mode='hide', legend_title_text='Місяць'
        )
        fig_top.update_xaxes(showticklabels=False)
        fig_top.update_layout(showlegend=False)
        st.plotly_chart(fig_top, use_container_width=True)


def plot_city_product_heatmap(pivot_df: pd.DataFrame):
    """Створює теплову карту продажів 'Місто-Продукт' з готової зведеної таблиці."""
    if pivot_df.empty:
        st.info("Немає даних для побудови теплової карти.")
        return
    fig = px.imshow(
        pivot_df, text_auto=True, aspect="auto", color_continuous_scale='Viridis',
        labels=dict(x="Продукт", y="Місто", color="Кількість")
    )
    fig.update_xaxes(side="top")
    st.plotly_chart(fig, use_container_width=True)


def plot_sales_dynamics(df: pd.DataFrame):
    """
    Створює адаптивний графік динаміки продажів та доходу.
    - Для >1 місяця: два окремі лінійні графіки.
    - Для 1 місяця: два окремі стовпчасті графіки.
    """
    if df.empty:
        st.info("Немає даних для побудови динаміки продажів.")
        return

    st.subheader("Динаміка продажів та доходу")
    df_chart = df.copy()
    has_revenue = 'revenue' in df_chart.columns and not df_chart['revenue'].isnull().all()
    unique_months_count = df_chart.groupby(['year', 'month']).ngroups

    # --- ЛОГІКА ДЛЯ ДЕКІЛЬКОХ МІСЯЦІВ ---
    if unique_months_count > 1:
        max_decade_per_month = df_chart.groupby(['year', 'month'])['decade'].transform('max')
        df_monthly_totals = df_chart[df_chart['decade'] == max_decade_per_month].copy()

        agg_funcs = {'quantity': 'sum'}
        if has_revenue:
            agg_funcs['revenue'] = 'sum'

        monthly_data = df_monthly_totals.groupby(['year', 'month']).agg(agg_funcs).reset_index()
        monthly_data = monthly_data.sort_values(by=['year', 'month'])
        monthly_data['month_label'] = monthly_data['month'].map(UKRAINIAN_MONTHS)
        monthly_data['x_axis_label'] = monthly_data['month_label'] + ' ' + monthly_data['year'].astype(str)

        # <<< ЗМІНА: Створюємо два окремі лінійні графіки >>>
        col1, col2 = st.columns(2)
        with col1:
            fig_qty = px.line(
                monthly_data,
                x='x_axis_label',
                y='quantity',
                markers=True,
                title="Динаміка продажів, уп.",
                labels={'x_axis_label': '', 'quantity': 'Кількість'},
                color_discrete_sequence=['#00656e']
            )
            fig_qty.update_layout(yaxis_title=None, xaxis_title=None)
            fig_qty.update_xaxes(type='category')
            fig_qty.update_layout(showlegend=False)
            fig_qty.update_layout(height=500)
            st.plotly_chart(fig_qty, use_container_width=True)

        with col2:
            if has_revenue:
                fig_rev = px.line(
                    monthly_data,
                    x='x_axis_label',
                    y='revenue',
                    markers=True,
                    title="Динаміка доходу, грн",
                    labels={'x_axis_label': '', 'revenue': 'Дохід'},
                    color_discrete_sequence=['#2e3d30']
                )
                fig_rev.update_layout(yaxis_title=None, xaxis_title=None)
                fig_rev.update_xaxes(type='category')
                fig_rev.update_layout(showlegend=False)
                fig_rev.update_layout(height=500)
                st.plotly_chart(fig_rev, use_container_width=True)
            else:
                st.info("Дані про дохід відсутні.")


    # --- ЛОГІКА ДЛЯ ОДНОГО МІСЯЦЯ ---
    else:
        sales_by_decade = df_chart.groupby('decade')['quantity'].sum().reset_index().sort_values('decade')
        sales_by_decade['actual_quantity'] = sales_by_decade['quantity'].diff().fillna(sales_by_decade['quantity'])
        sales_by_decade['x_axis_label'] = sales_by_decade['decade'].astype(int).astype(str) + "-а декада"

        month_name = UKRAINIAN_MONTHS.get(df_chart['month'].iloc[0], "")

        col1, col2 = st.columns(2)

        with col1:
            fig_qty = px.bar(
                sales_by_decade, x='x_axis_label', y='actual_quantity', text='actual_quantity',
                title=f"Продажі за декадами, уп.",
                labels={'x_axis_label': '', 'actual_quantity': 'Кількість'},
                color_discrete_sequence=['#00656e']
            )
            fig_qty.update_traces(texttemplate='%{text:.0f}', textposition='outside')
            fig_qty.update_traces(textfont_color='black')
            fig_qty.update_layout(uniformtext_minsize=8, yaxis_title=None, xaxis_title=None)
            fig_qty.update_layout(showlegend=False)
            fig_qty.update_layout(height=500)
            st.plotly_chart(fig_qty, use_container_width=True)

        with col2:
            if has_revenue:
                revenue_by_decade = df_chart.groupby('decade')['revenue'].sum().reset_index().sort_values('decade')
                revenue_by_decade['actual_revenue'] = revenue_by_decade['revenue'].diff().fillna(
                    revenue_by_decade['revenue'])
                revenue_by_decade['x_axis_label'] = revenue_by_decade['decade'].astype(int).astype(str) + "-а декада"

                fig_rev = px.bar(
                    revenue_by_decade, x='x_axis_label', y='actual_revenue', text='actual_revenue',
                    title=f"Дохід за декадами, грн",
                    labels={'x_axis_label': '', 'actual_revenue': 'Дохід'},
                    color_discrete_sequence=['#5f7355']
                )
                fig_rev.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                fig_rev.update_traces(textfont_color='black')
                fig_rev.update_layout(uniformtext_minsize=8, yaxis_title=None, xaxis_title=None)
                fig_rev.update_layout(showlegend=False)
                fig_rev.update_layout(height=500)
                st.plotly_chart(fig_rev, use_container_width=True)
            else:
                st.info("Дані про дохід відсутні.")
