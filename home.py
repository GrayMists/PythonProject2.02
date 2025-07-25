import streamlit as st
from streamlit_option_menu import option_menu
from core.data_loader import fetch_all_sales_data
from pages_logic import sales_page, upload_page  # Логіка для сторінок імпортується сюди
from utils import supabase  # Імпортуємо supabase для прямих запитів

# --- Налаштування сторінки ---
st.set_page_config(
    page_title="Аналіз Продажів",
    layout="centered",
    initial_sidebar_state="expanded"
)


# --- Функція для завантаження територій ---
@st.cache_data(ttl=3600)
def load_territories_for_region(region_id):
    """Завантажує території для конкретного регіону."""
    if not region_id:
        return []
    try:
        # Припущення: у вас є таблиця 'territory' з колонками 'name', 'technical_name', 'region_id'
        response = supabase.table("territory").select("name, technical_name").eq("region_id", region_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Помилка завантаження територій: {e}")
        return []


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

    # --- ФІЛЬТР РЕГІОНІВ СТАВ ГОЛОВНИМ ---
    # Використовуємо функцію завантаження з модуля upload_page, як і було раніше
    all_regions_data = upload_page.load_data_from_supabase("region")
    if all_regions_data:
        region_names = ["Оберіть регіон..."] + [r['name'] for r in all_regions_data]
        selected_region_name = st.selectbox("1. Оберіть регіон:", region_names)

        # --- ІНШІ ФІЛЬТРИ З'ЯВЛЯЮТЬСЯ ПІСЛЯ ВИБОРУ РЕГІОНУ ---
        if selected_region_name != "Оберіть регіон...":
            # Знаходимо ID обраного регіону для завантаження територій
            selected_region_id = next(
                (r['id'] for r in all_regions_data if r['name'] == selected_region_name), None
            )

            # --- ДИНАМІЧНЕ ФОРМУВАННЯ СПИСКУ ТЕРИТОРІЙ ---
            territories_data = load_territories_for_region(selected_region_id)

            if territories_data:
                TERRITORY_MAP = {item['name']: item['technical_name'] for item in territories_data}
                TERRITORY_MAP = {"Всі території": "Всі"} | TERRITORY_MAP
            else:
                TERRITORY_MAP = {"Всі території": "Всі"}
                st.info("Для цього регіону території не знайдено.")

            available_territory_names = list(TERRITORY_MAP.keys())
            selected_territory_name_from_map = st.selectbox("2. Територія:", available_territory_names)
            territory_to_pass = TERRITORY_MAP[selected_territory_name_from_map]

            # Інші фільтри
            available_lines = ["Всі", "Лінія 1", "Лінія 2"]  # Можна також завантажувати динамічно
            selected_line = st.selectbox("3. Лінійка:", available_lines)

            month_map = {
                "Січень": 1, "Лютий": 2, "Березень": 3, "Квітень": 4,
                "Травень": 5, "Червень": 6, "Липень": 7, "Серпень": 8,
                "Вересень": 9, "Жовтень": 10, "Листопад": 11, "Грудень": 12
            }
            selected_month_names = st.multiselect(
                "4. Оберіть місяці (якщо не обрано - всі):",
                options=list(month_map.keys())
            )
            months_to_load = [f"{month_map[name]:02d}" for name in selected_month_names]

            if st.button("Отримати дані", type="primary"):
                st.session_state.selected_territory_value = territory_to_pass
                with st.spinner("Завантаження даних... Це може зайняти деякий час."):
                    # --- ПЕРЕДАЄМО НАЗВУ РЕГІОНУ У ФУНКЦІЮ ---
                    st.session_state.sales_df_full = fetch_all_sales_data(
                        region_name=selected_region_name,
                        territory=territory_to_pass,
                        line=selected_line,
                        months=months_to_load
                    )
                st.success("Дані успішно завантажено!")
                if 'sales_df_full' in st.session_state and not st.session_state.sales_df_full.empty:
                    st.info(f"Завантажено {len(st.session_state.sales_df_full)} записів.")
                else:
                    st.warning("За обраними фільтрами дані не знайдено.")
    else:
        st.warning("Не вдалося завантажити список регіонів.")

# --- Відображення обраної сторінки ("Роутер") ---
if selected_page == "Аналіз продажів":
    sales_page.show()
elif selected_page == "Завантаження даних":
    upload_page.show()
