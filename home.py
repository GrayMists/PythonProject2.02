import streamlit as st
from streamlit_option_menu import option_menu
from core.data_loader import fetch_all_sales_data
from pages_logic import sales_page, upload_page  # Логіка для сторінок імпортується сюди

# --- Налаштування сторінки ---
# Робимо це один раз на початку
st.set_page_config(
    page_title="Аналіз Продажів",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Бічна панель з меню та глобальними фільтрами ---
with st.sidebar:
    selected_page = option_menu(
        menu_title="Головне меню",
        options=["Аналіз продажів", "Завантаження даних"],
        icons=["bar-chart-line-fill", "cloud-upload-fill"],
        menu_icon="cast",
        default_index=0,
    )

    st.title("Панель управління")
    st.header("Глобальні фільтри")

    # Створюємо словник для співставлення імен та значень
    TERRITORY_MAP = {
        "Всі території": "Всі",
        "Тарас і Марійка": "Територія 1",
        "Наталя та Ігор": "Територія 2",
    }

    # Для вибору користувачеві показуємо тільки ключі (зрозумілі імена)
    available_territory_names = list(TERRITORY_MAP.keys())
    selected_territory_name = st.selectbox("Територія:", available_territory_names)

    # Отримуємо технічне значення, яке відповідає обраному імені
    territory_to_pass = TERRITORY_MAP[selected_territory_name]

    available_lines = ["Всі", "Лінія 1", "Лінія 2"]
    selected_line = st.selectbox("Лінійка:", available_lines)

    month_map = {
        "Січень": 1, "Лютий": 2, "Березень": 3, "Квітень": 4,
        "Травень": 5, "Червень": 6, "Липень": 7, "Серпень": 8,
        "Вересень": 9, "Жовтень": 10, "Листопад": 11, "Грудень": 12
    }

    selected_month_names = st.multiselect(
        "Оберіть місяці (якщо не обрано - всі):",
        options=list(month_map.keys())
    )

    months_to_load = [f"{month_map[name]:02d}" for name in selected_month_names]

    if st.button("Отримати дані", type="primary"):
        # Зберігаємо обрану територію в стані сесії для використання на інших сторінках
        st.session_state.selected_territory_value = territory_to_pass

        with st.spinner("Завантаження даних... Це може зайняти деякий час."):
            # У функцію передаємо вже технічне значення території
            st.session_state.sales_df_full = fetch_all_sales_data(
                territory=territory_to_pass,
                line=selected_line,
                months=months_to_load
            )
        st.success("Дані успішно завантажено!")
        if 'sales_df_full' in st.session_state and not st.session_state.sales_df_full.empty:
            st.info(f"Завантажено {len(st.session_state.sales_df_full)} записів.")
        else:
            st.warning("За обраними фільтрами дані не знайдено.")

# --- Відображення обраної сторінки ("Роутер") ---
if selected_page == "Аналіз продажів":
    sales_page.show()
elif selected_page == "Завантаження даних":
    # Це місце для вашої сторінки завантаження
    upload_page.show()