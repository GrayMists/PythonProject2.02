import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Словник для перекладу номерів місяців у назви українською
UKRAINIAN_MONTHS = {
    1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень",
    5: "Травень", 6: "Червень", 7: "Липень", 8: "Серпень",
    9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень"
}


def plot_top_products_bar_chart(df_top: pd.DataFrame, df_bottom: pd.DataFrame):
    """
    Створює стовпчасті діаграми для ТОП та анти-ТОП продуктів.
    Автоматично створює розбивку по місяцях, якщо їх декілька.
    """
    if df_top.empty:
        st.info("Немає даних для побудови графіків продуктів.")
        return

    # Додаємо колонку з назвами місяців для красивих легенд на графіку
    df_top['month_name'] = pd.to_numeric(df_top['month']).map(UKRAINIAN_MONTHS)
    df_bottom['month_name'] = pd.to_numeric(df_bottom['month']).map(UKRAINIAN_MONTHS)

    # Агрегуємо дані ПЕРЕД побудовою графіка
    df_top_agg = df_top.groupby(['product_name', 'month_name'])['quantity'].sum().reset_index()
    df_bottom_agg = df_bottom.groupby(['product_name', 'month_name'])['quantity'].sum().reset_index()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**ТОП-5 найбільш продаваних продуктів:**")
        # Сортуємо продукти за загальною кількістю
        top_order = df_top_agg.groupby('product_name')['quantity'].sum().sort_values(ascending=True).index

        fig_top = px.bar(
            df_top_agg,
            y='product_name',
            x='quantity',
            color='month_name',
            orientation='h',
            title="Найбільш продавані",
            labels={'quantity': 'Кількість', 'product_name': 'Продукт', 'month_name': 'Місяць'},
            category_orders={'product_name': top_order}
        )

        # --- НОВИЙ БЛОК: Додаємо загальну суму в кінці стовпця ---
        totals_top = df_top_agg.groupby('product_name')['quantity'].sum()
        for product in top_order:
            total_val = totals_top[product]
            fig_top.add_annotation(
                y=product,
                x=total_val,
                text=f"<b>{total_val}</b>",
                showarrow=False,
                xanchor='left',
                xshift=5,
                font=dict(color="white")
            )

        # Прибираємо підписи на осях
        fig_top.update_layout(
            yaxis_title=None,
            xaxis_title=None,
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )
        fig_top.update_xaxes(showticklabels=False)
        st.plotly_chart(fig_top, use_container_width=True)

    with col2:
        st.markdown("**ТОП-5 найменш продаваних продуктів:**")
        # Сортуємо продукти за загальною кількістю
        bottom_order = df_bottom_agg.groupby('product_name')['quantity'].sum().sort_values(ascending=True).index

        fig_bottom = px.bar(
            df_bottom_agg,
            y='product_name',
            x='quantity',
            color='month_name',
            orientation='h',
            title="Найменш продавані",
            labels={'quantity': 'Кількість', 'product_name': 'Продукт', 'month_name': 'Місяць'},
            category_orders={'product_name': bottom_order}
        )

        # --- НОВИЙ БЛОК: Додаємо загальну суму в кінці стовпця ---
        totals_bottom = df_bottom_agg.groupby('product_name')['quantity'].sum()
        for product in bottom_order:
            total_val = totals_bottom[product]
            fig_bottom.add_annotation(
                y=product,
                x=total_val,
                text=f"<b>{total_val}</b>",
                showarrow=False,
                xanchor='left',
                xshift=5,
                font=dict(color="white")
            )

        # Прибираємо підписи на осях
        fig_bottom.update_layout(
            yaxis_title=None,
            xaxis_title=None,
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )
        fig_bottom.update_xaxes(showticklabels=False)
        st.plotly_chart(fig_bottom, use_container_width=True)


def plot_city_product_heatmap(pivot_df: pd.DataFrame):
    """Створює теплову карту продажів 'Місто-Продукт' з готової зведеної таблиці."""
    if pivot_df.empty:
        st.info("Немає даних для побудови теплової карти.")
        return

    fig = px.imshow(
        pivot_df,
        text_auto=True,
        aspect="auto",
        color_continuous_scale='Viridis',
        labels=dict(x="Продукт", y="Місто", color="Кількість")
    )
    fig.update_xaxes(side="top")
    st.plotly_chart(fig, use_container_width=True)


def plot_sales_dynamics(df: pd.DataFrame):
    """Створює лінійний графік динаміки продажів з українськими назвами місяців."""
    if df.empty:
        st.info("Немає даних для побудови динаміки продажів.")
        return

    st.subheader("Динаміка продажів за обраний період")
    df_chart = df.copy()

    df_chart['year'] = pd.to_numeric(df_chart['year'])
    df_chart['month'] = pd.to_numeric(df_chart['month'])
    monthly_sales = df_chart.groupby(['year', 'month'])['quantity'].sum().reset_index()
    monthly_sales = monthly_sales.sort_values(by=['year', 'month'])
    monthly_sales['month_label'] = monthly_sales['month'].map(UKRAINIAN_MONTHS)
    monthly_sales['x_axis_label'] = monthly_sales['month_label'] + ' ' + monthly_sales['year'].astype(str)

    fig = px.line(
        monthly_sales,
        x='x_axis_label',
        y='quantity',
        markers=True,
        title="Загальна кількість проданих упаковок по місяцях",
        labels={'x_axis_label': 'Місяць', 'quantity': 'Кількість'}
    )
    fig.update_xaxes(type='category')
    st.plotly_chart(fig, use_container_width=True)
