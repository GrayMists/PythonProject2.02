import streamlit as st
from streamlit_option_menu import option_menu

import sales_page  # Імпортуємо файл сторінки "Продажі"
import upload_page  # Імпортуємо файл сторінки "Завантаження"

# --- Налаштування сторінки ---
st.set_page_config(
    page_title="Аналітичний Дашборд",
    page_icon="📊",
    layout="centered"
)

# --- Головна частина застосунку (навігація) ---
with st.sidebar:
    selected = option_menu(
        menu_title="Головне меню",
        options=["Продажі", "Завантаження даних"],
        icons=["bar-chart-line", "upload"],
        menu_icon="cast",
        default_index=0,
        key="main_menu"
    )

    # Контекстні фільтри для сторінки "Продажі"
    if selected == "Продажі":
        st.sidebar.header("Фільтри")
        selected_territory = st.sidebar.selectbox(
            "Оберіть територію:",
            ["Всі", "Територія 1", "Територія 2"],
            key="territory_filter"
        )
        selected_line = st.sidebar.selectbox(
            "Оберіть лінію:",
            ["Всі", "Лінія 1", "Лінія 2"],
            key="line_filter"
        )

        month_map = {
            "Січень": 1, "Лютий": 2, "Березень": 3, "Квітень": 4,
            "Травень": 5, "Червень": 6, "Липень": 7, "Серпень": 8,
            "Вересень": 9, "Жовтень": 10, "Листопад": 11, "Грудень": 12
        }

        selected_month_names = st.sidebar.multiselect(
            "Оберіть місяці (якщо не обрано - всі):",
            options=list(month_map.keys()),
            key="month_filter"
        )

        # --- ЗМІНА ТУТ ---
        # Конвертуємо назви місяців у числа, а потім одразу в рядки (текст)
        selected_month_strings = [f"{month_map[name]:02d}" for name in selected_month_names]

        if st.sidebar.button("Отримати дані", type="primary", key="get_data_button"):
            # Передаємо у функцію список рядків
            df_full = sales_page.fetch_all_sales_data(
                selected_territory,
                selected_line,
                selected_month_strings  # <-- Тепер це список рядків ['1', '2', ...]
            )
            st.session_state['sales_df_full'] = df_full
            # Скидаємо значення залежних фільтрів при новому запиті
            if 'city_filter' in st.session_state:
                st.session_state.city_filter = "Всі"
            if 'street_filter' in st.session_state:
                st.session_state.street_filter = "Всі"

# Виклик відповідної функції для відображення сторінки
if selected == "Продажі":
    sales_page.show()

if selected == "Завантаження даних":
    upload_page.show()
