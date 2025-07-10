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

def plot_top_products_bar_chart(top_products: pd.Series, rev_top_products: pd.Series):
    """Створює стовпчасті діаграми для ТОП та анти-ТОП продуктів."""
    if top_products.empty:
        st.info("Немає даних для побудови графіків продуктів.")
        return

    col1, col2 = st.columns(2)
    with col1:
        fig_top = px.bar(
            top_products,
            orientation='h',
            text_auto=True,
            title="ТОП-5 найбільш продаваних продуктів",
            labels={'value': 'Кількість', 'product_name': 'Продукт'},
            color_discrete_sequence = ['#4B6F44']
        )
        fig_top.update_layout(showlegend=False, yaxis_title=None)
        st.plotly_chart(fig_top, use_container_width=True)

    with col2:
        fig_rev = px.bar(
            rev_top_products,
            orientation='h',
            text_auto=True,
            title="ТОП-5 найменш продаваних продуктів",
            labels={'value': 'Кількість', 'product_name': 'Продукт'},
            color_discrete_sequence=['#FF7F0E']
        )
        fig_rev.update_layout(showlegend=False, yaxis_title=None)
        st.plotly_chart(fig_rev, use_container_width=True)


def plot_city_product_heatmap(df: pd.DataFrame):
    """Створює теплову карту продажів 'Місто-Продукт'."""
    if df.empty:
        st.info("Немає даних для побудови теплової карти.")
        return

    st.subheader("Теплова карта: Міста та Продукти")
    city_product_pivot = df.pivot_table(
        index='Місто',
        columns='product_name',
        values='quantity',
        aggfunc='sum',
        fill_value=0
    )

    fig = px.imshow(
        city_product_pivot,
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

    # 1. Переконуємось, що місяць та рік є числовими для коректного сортування
    df_chart['year'] = pd.to_numeric(df_chart['year'])
    df_chart['month'] = pd.to_numeric(df_chart['month'])

    # 2. Групуємо дані по року та місяцю
    monthly_sales = df_chart.groupby(['year', 'month'])['quantity'].sum().reset_index()

    # 3. Сортуємо дані хронологічно, щоб лінія на графіку йшла правильно
    monthly_sales = monthly_sales.sort_values(by=['year', 'month'])

    # 4. Створюємо текстову мітку для осі X, яка буде відображатись на графіку
    monthly_sales['month_label'] = monthly_sales['month'].map(UKRAINIAN_MONTHS)
    monthly_sales['x_axis_label'] = monthly_sales['month_label'] + ' ' + monthly_sales['year'].astype(str)

    # 5. Будуємо графік, використовуючи нові текстові мітки для осі X
    fig = px.line(
        monthly_sales,
        x='x_axis_label',  # Використовуємо колонку з мітками "Місяць Рік"
        y='quantity',
        markers=True,
        title="Загальна кількість проданих упаковок по місяцях",
        labels={'x_axis_label': 'Місяць', 'quantity': 'Кількість'}
    )

    # 6. Вказуємо, що вісь X є 'category', щоб зберегти наш порядок і назви
    fig.update_xaxes(type='category')

    st.plotly_chart(fig, use_container_width=True)

