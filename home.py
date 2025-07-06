import streamlit as st
import pandas as pd
import re
from thefuzz import process, fuzz
import io
from supabase import create_client, Client

# --- Еталонні списки та словники ---

# Словник для визначення лінії препарату
PRODUCTS_DICT = {
    "Аденофіт-форте №60": "Лінія 1",
    "Анксіомедін №20": "Лінія 1",
    "Анксіомедін №60": "Лінія 1",
    "Антистрес №30": "Лінія 1",
    "Антистрес №60": "Лінія 1",
    "Астадінол 2000 №30": "Лінія 1",
    "Астадінол 4000 №30": "Лінія 1",
    "Атеродінол №60": "Лінія 2",
    "Візінорм №30": "Лінія 2",
    "Візінорм №60": "Лінія 2",
    "Глюцемедін №30": "Лінія 1",
    "Глюцемедін №60": "Лінія 1",
    "Депріліум №30": "Лінія 1",
    "Дуонефрил №30": "Лінія 1",
    "Дуонефрил №60": "Лінія 1",
    "Дуонефрил №90": "Лінія 1",
    "Дуонефрил-500 №30": "Лінія 1",
    "Дуонефрил-500 №60": "Лінія 1",
    "Дуонефрил-500 №90": "Лінія 1",
    "Зобофіт №60": "Лінія 2",
    "Зобофіт ДУО №30": "Лінія 2",
    "Зобофіт ДУО №60": "Лінія 2",
    "Зобофіт Селен №60": "Лінія 2",
    "Імунсил D3 №30": "Лінія 1",
    "Імунсил D3 №60": "Лінія 1",
    "Імунсил D3 ДУО №30": "Лінія 1",
    "Імунсил D3 ДУО №60": "Лінія 1",
    "Індомірол №30": "Лінія 1",
    "Індомірол №60": "Лінія 1",
    "Індомірол-М №30": "Лінія 1",
    "Індомірол-М №60": "Лінія 1",
    "Індомірол-форте №60": "Лінія 1",
    "Індомірол-М форте №60": "Лінія 1",
    "Інулін-Нутрімед №60": "Лінія 1",
    "Камавіт-форте №60": "Лінія 2",
    "Ліводінол №60": "Лінія 2",
    "Ліводінол Макс №40": "Лінія 2",
    "Меномедін №30": "Лінія 2",
    "Меномедін-М №60": "Лінія 2",
    "Монморол №30": "Лінія 1",
    "Монморол №60": "Лінія 1",
    "Неопрост-форте №30": "Лінія 2",
    "Неопрост-форте №60": "Лінія 2",
    "Оварімедін №60": "Лінія 2",
    "Ресверазин №30": "Лінія 2",
    "Ресверазин №60": "Лінія 2",
    "Сономедін №20": "Лінія 1",
    "Церебровітал №30": "Лінія 2",
    "Церебровітал №60": "Лінія 2",
    "Церебровітал Актив №30": "Лінія 2",
    "Цинкоферол-4000 №30": "Лінія 1"
}

CANONICAL_CITIES = [
    "Бережани", "Борщів", "Бучач", "Велика Березовиця", "Великі Дедеркали",
    "Вишнівець", "Городниця", "Гримайлів", "Гусятин", "Дружба", "Заліщики",
    "Збараж", "Золотий Потік", "Іване-Пусте", "Клювинці", "Козова", "Копичинці",
    "Коропець", "Кременець", "Ланівці", "Мельниця-Подільська", "Микулинці",
    "Мишковичі", "Монастириська", "Нагірянка", "Озерна", "Підгайці",
    "Підволочиськ", "Почаїв", "Скала-Подільська", "Скалат", "Струсів",
    "Теребовля", "Тернопіль", "Товсте", "Хоростків", "Чортків", "Шумськ"
]

STREET_TYPE_MAP = {
    "проспект": "просп.", "просп.": "просп.", "пр-т": "просп.",
    "вулиця": "вул.", "вул.": "вул.",
    "бульвар": "бул.", "бул-р": "бул.", "б-р": "бул.",
    "площа": "пл.", "пл.": "пл.",
    "майдан": "м-н.", "м-н": "м-н."
}

CANONICAL_STREET_NAMES = [
    "15-го Квітня", "Антона Манастирського", "Бережанська", "Богдана Хмельницького",
    "Богдана Лепкого", "Бродівська", "В. Стуса", "Василя Симоненка", "Возз'єднання",
    "Волинська", "Володимира Громницького", "Володимира Лучаковського",
    "В'ячеслава Чорновола", "Галицька", "Генерала Мирона Тарнавського",
    "Генерала Шухевича", "Героїв Євромайдану", "Героїв Крут", "Гетьмана Івана Мазепи",
    "Горбача", "Данила Галицького", "Дмитра Вишневецького", "Дорошенка", "Дружби",
    "Дубенська", "Енергетична", "Живова", "Замкова", "Збаразька", "Злуки",
    "Івана Мазепи", "Івана Франка", "Каганця Марка", "Карпенка", "Київська",
    "Клінічна", "Князя Василька", "Князя Володимира", "Кондри", "Л.Українки",
    "Лесі Українки", "Лосятинська", "Льотчиків-Визволителів", "Маковея",
    "Миколи Карпенка", "Микулинецька", "Миру", "Михайла Грушевського",
    "Михайла Паращука", "Міцкевича", "Мстислава Патріарха", "Мстислава",
    "Наливайка", "Незалежності", "Нова", "Новий Світ", "Олеся Гончара",
    "Осипа Маковея", "Павлова", "Патріарха Любомира Гузара", "Перемоги", "Перля",
    "Петра Герети", "Петра Дорошенка", "Петлюри", "Пирогова", "Підгаєцька",
    "Поліська", "Поштова", "Ринок", "Романа Гралюка", "Романа Купчинського",
    "Руська", "Сагайдачного", "Садова", "Симона Петлюри", "Січових Стрільців",
    "Степана Бандери", "Степана Будного", "Стефаника", "Тараса Шевченка",
    "Текстильна", "Тернопільська", "Торговиця", "Тролейбусна", "Українська",
    "Федьковича", "Центральна", "Шкільна", "Шпитальна", "Юліана Опільського"
]


# --- Функції для обробки адрес ---

def parse_full_address(address: str) -> dict:
    """
    Алгоритмічний парсер для адрес, яких немає у "золотому" словнику.
    """
    result = {'city': None, 'street': None, 'number': None, 'territory': None}
    if not isinstance(address, str) or not address.strip():
        return result

    work_address = address.lower().strip()
    work_address = re.sub(r'\b\w+?ська\s+обл\.?,?', '', work_address).strip(' ,')
    work_address = re.sub(r'[,\s]*\b(прим|кв|квартира|пом|приміщення|корпус|корп|кнп|трц|тор|кцрл)\b.*', '',
                          work_address)

    city_str, rest_of_address = None, work_address
    city_pattern = re.compile(r'^(м|смт|селище|місто|с)\.?\s*([а-яґґ\'\-]+)')
    city_match = city_pattern.search(work_address)

    if city_match:
        city_candidate = city_match.group(2)
        best_match = process.extractOne(city_candidate, CANONICAL_CITIES, score_cutoff=85)
        if best_match:
            city_str = best_match[0]
            rest_of_address = work_address[city_match.end():].strip(' ,')
    else:
        best_match = process.extractOne(work_address, CANONICAL_CITIES, scorer=fuzz.WRatio, score_cutoff=88)
        if best_match and work_address.startswith(best_match[0].lower()):
            city_str = best_match[0]
            rest_of_address = work_address[len(city_str):].strip(' ,')

    result['city'] = city_str

    street_part = rest_of_address
    num_pattern = r'\b\d+[\w\-/]*\b'
    all_numbers = re.findall(num_pattern, rest_of_address)

    if all_numbers:
        number_str = all_numbers[-1]
        result['number'] = number_str
        number_match_pos = re.search(r'\b' + re.escape(number_str) + r'\b', rest_of_address)
        if number_match_pos:
            street_part = rest_of_address[:number_match_pos.start()].strip(' ,')

    street_type, street_name_candidate = "вул.", street_part
    sorted_street_types = sorted(STREET_TYPE_MAP.keys(), key=len, reverse=True)
    for key in sorted_street_types:
        pattern = r'^' + re.escape(key) + r'\b'
        if re.search(pattern, street_name_candidate):
            street_type = STREET_TYPE_MAP[key]
            street_name_candidate = re.sub(pattern, '', street_name_candidate).strip()
            break

    street_name_candidate = re.sub(r'\bбуд\.?\b', '', street_name_candidate)
    street_name_candidate = re.sub(r'\b[а-яґґ]\.\s*', '', street_name_candidate)
    street_name_candidate = street_name_candidate.strip(' ,-./')

    best_street_match = process.extractOne(street_name_candidate, CANONICAL_STREET_NAMES, score_cutoff=80)
    street_name = best_street_match[0] if best_street_match else street_name_candidate.title()

    if street_name:
        result['street'] = f"{street_type} {street_name}"

    return result


@st.cache_data(ttl=3600)  # Кешуємо дані на 1 годину
def load_golden_records_from_supabase() -> dict:
    """
    Завантажує "золоті" записи з таблиці Supabase і перетворює їх у словник.
    """
    try:
        url = "https://vimswywxzejgyvxjzuvf.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZpbXN3eXd4emVqZ3l2eGp6dXZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4NTk5NDYsImV4cCI6MjA2MTQzNTk0Nn0.bqcMzJaUet9yPsUEuXe6cqvKjzOBOBvQzBG6eXFl0VU"
        supabase: Client = create_client(url, key)

        table_name = "golden_addres"

        response = supabase.table(table_name).select("*").execute()

        data = response.data
        if not data:
            st.warning(f"Таблиця '{table_name}' у Supabase порожня або не знайдена.")
            return {}

        golden_map = {}
        for row in data:
            key = str(row.get("Факт.адреса доставки")).lower().strip()
            value = {
                'city': row.get("Місто"),
                'street': row.get("Вулиця"),
                'number': str(row.get("Номер будинку")) if row.get("Номер будинку") is not None else None,
                'territory': row.get("Територія")
            }
            golden_map[key] = value

        st.success(f"Успішно завантажено {len(golden_map)} 'золотих' записів з Supabase.")
        return golden_map

    except Exception as e:
        st.error(f"Помилка при підключенні або завантаженні даних з Supabase: {e}")
        return {}


def process_address_hybrid(address: str, golden_map: dict) -> dict:
    """
    Гібридна функція: спочатку шукає у словнику, потім використовує парсер.
    """
    lookup_key = str(address).lower().strip()
    golden_result = golden_map.get(lookup_key)

    if golden_result:
        return golden_result
    else:
        return parse_full_address(address)


# --- UI Streamlit ---

st.set_page_config(layout="wide")
st.title("🚀 Інструмент для очищення та стандартизації адрес")
st.write(
    "Завантажте ваш Excel-файл з адресами. Еталонні дані будуть автоматично завантажені з бази даних Supabase."
)

golden_map = load_golden_records_from_supabase()

uploaded_file = st.file_uploader(
    "Виберіть Excel-файл з адресами для обробки",
    type=['xlsx', 'xls']
)

if uploaded_file is not None and golden_map:
    try:
        df = pd.read_excel(uploaded_file)

        required_columns = ['Регіон', 'Факт.адреса доставки', 'Найменування']
        if not all(col in df.columns for col in required_columns):
            st.error(
                f"Помилка: В основному файлі відсутня одна з необхідних колонок: {', '.join(required_columns)}."
            )
        else:
            st.info(f"Основний файл '{uploaded_file.name}' успішно завантажено. Всього знайдено {len(df)} рядків.")

            df_filtered = df[df['Регіон'] == '24. Тернопіль'].copy()

            if df_filtered.empty:
                st.warning("У файлі не знайдено жодного рядка з регіоном '24. Тернопіль'. Подальша обробка неможлива.")
            else:
                st.info(
                    f"Після фільтрації за регіоном '24. Тернопіль' для обробки залишилось **{len(df_filtered)}** рядків."
                )

                with st.spinner("✨ Обробляємо адреси та додаємо дані..."):
                    parsed_addresses = df_filtered['Факт.адреса доставки'].apply(process_address_hybrid,
                                                                                 golden_map=golden_map)

                    parsed_df = pd.json_normalize(parsed_addresses)

                    # ⭐️ ОНОВЛЕНО: Перейменовуємо нові колонки на англійські назви
                    parsed_df = parsed_df.rename(columns={
                        'city': 'City',
                        'street': 'Street',
                        'number': 'House_Number',
                        'territory': 'Territory'
                    })

                    df_filtered.reset_index(drop=True, inplace=True)
                    parsed_df.reset_index(drop=True, inplace=True)

                    # ⭐️ ОНОВЛЕНО: Видаляємо тільки ті старі колонки, які будуть замінені
                    # Оригінальна колонка 'Місто' залишається недоторканою
                    df_filtered.drop(columns=['Вулиця', 'Номер будинку', 'Територія'], inplace=True, errors='ignore')

                    result_df = pd.concat([df_filtered, parsed_df], axis=1)

                    # ⭐️ ОНОВЛЕНО: Створюємо нову колонку з англійською назвою
                    result_df['Product_Line'] = result_df['Найменування'].str[3:].map(PRODUCTS_DICT)

                st.success("Готово! Адреси успішно оброблено.")
                st.dataframe(result_df)

    except Exception as e:
        st.error(f"Виникла помилка при обробці файлу: {e}")
