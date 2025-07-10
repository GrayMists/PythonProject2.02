import streamlit as st
from streamlit_option_menu import option_menu
from core.data_loader import fetch_all_sales_data
from pages_logic import sales_page, upload_page # Логіка для сторінок імпортується сюди

# --- Налаштування сторінки ---
# Робимо це один раз на початку
st.set_page_config(
    page_title="Аналіз Продажів",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Бічна панель з меню та глобальними фільтрами ---
# Архітектурне рішення: фільтри для завантаження даних є глобальними і живуть на бічній панелі.
# Це дозволяє завантажити дані один раз, а потім аналізувати їх на різних сторінках без перезавантаження.
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

    # У реальному додатку ці списки можна завантажувати з бази даних
    available_territories = ["Всі", "Територія 1", "Територія 2", "Територія 3"]
    available_lines = ["Всі", "Лінія 1", "Лінія 2"]

    selected_territory = st.selectbox("Територія:", available_territories)
    selected_line = st.selectbox("Лінійка:", available_lines)

    # --- ВИПРАВЛЕНА ЛОГІКА ВИБОРУ МІСЯЦІВ ---
    # Повернено до оригінального, робочого варіанту
    month_map = {
        "Січень": 1, "Лютий": 2, "Березень": 3, "Квітень": 4,
        "Травень": 5, "Червень": 6, "Липень": 7, "Серпень": 8,
        "Вересень": 9, "Жовтень": 10, "Листопад": 11, "Грудень": 12
    }

    selected_month_names = st.multiselect(
        "Оберіть місяці (якщо не обрано - всі):",
        options=list(month_map.keys())
    )

    # Конвертуємо назви місяців у список двозначних рядків (напр. "05"),
    # як того очікує база даних.
    months_to_load = [f"{month_map[name]:02d}" for name in selected_month_names]

    if st.button("Отримати дані", type="primary"):
        with st.spinner("Завантаження даних... Це може зайняти деякий час."):
            # Викликаємо функцію з окремого модуля data_loader
            st.session_state.sales_df_full = fetch_all_sales_data(
                territory=selected_territory,
                line=selected_line,
                months=months_to_load
            )
        st.success("Дані успішно завантажено!")
        if 'sales_df_full' in st.session_state and not st.session_state.sales_df_full.empty:
            st.info(f"Завантажено {len(st.session_state.sales_df_full)} записів.")
        else:
            st.warning("За обраними фільтрами дані не знайдено.")


# --- Відображення обраної сторінки ("Роутер") ---
# Цей блок викликає відповідну функцію з модуля pages_logic на основі вибору в меню
if selected_page == "Аналіз продажів":
    sales_page.show()
elif selected_page == "Завантаження даних":
    # upload_page.show() # Тут буде виклик функції для сторінки завантаження
    st.title("Сторінка завантаження даних")
    st.info("Ця частина додатку в розробці.")
