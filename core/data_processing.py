import pandas as pd
import numpy as np
from datetime import date, timedelta
from workalendar.europe import Ukraine  # Бібліотека для розрахунку робочих днів в Україні


# --- Існуючі функції без змін ---

def create_full_address(df: pd.DataFrame) -> pd.DataFrame:
    """Створює єдину колонку 'full_address' для групування."""
    if 'full_address' not in df.columns:
        df['full_address'] = (
                df['city'].astype(str).fillna('') + ", " +
                df['street'].astype(str).fillna('') + ", " +
                df['house_number'].astype(str).fillna('')
        ).str.strip(' ,')
    return df


# --- ОНОВЛЕНА ФУНКЦІЯ compute_actual_sales ---

def compute_actual_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Розраховує "чисті" продажі між декадами з виправленою логікою.
    Ця версія враховує дистриб'ютора та клієнта, щоб розрахунки велися окремо для кожного,
    і включає ретельну очистку текстових полів.
    Припускається, що 'quantity' у вхідному DataFrame є КУМУЛЯТИВНОЮ сумою продажів
    до кінця відповідної декади.
    """
    # Початкова перевірка на наявність критично важливих колонок
    required_cols = ['decade', 'distributor', 'product_name', 'quantity', 'year', 'month', 'city', 'street', 'house_number', 'new_client']
    for col in required_cols:
        if col not in df.columns:
            print(f"Попередження: Відсутня необхідна колонка '{col}'. Повертаю порожній DataFrame.")
            return pd.DataFrame(
                columns=['distributor', 'product_name', 'full_address', 'year', 'month', 'decade', 'actual_quantity', 'new_client'])

    if df.empty:
        print("Попередження: Вхідний DataFrame порожній. Повертаю порожній DataFrame.")
        return pd.DataFrame(
            columns=['distributor', 'product_name', 'full_address', 'year', 'month', 'decade', 'actual_quantity', 'new_client'])

    # --- КРОК ОЧИЩЕННЯ ДАНИХ ---
    # Примусово видаляємо зайві пробіли з ключових текстових полів.
    text_cols_to_clean = ['distributor', 'product_name', 'city', 'street', 'house_number', 'new_client']
    for col in text_cols_to_clean:
        if col in df.columns: # Перевіряємо наявність колонки перед очищенням
            df[col] = df[col].fillna('').astype(str).str.strip()

    # Створення повної адреси відбувається ПІСЛЯ очищення її компонентів
    # Використовуємо вашу оригінальну функцію create_full_address
    df = create_full_address(df)
    df = df[df['full_address'] != '']
    # Перетворюємо 'decade' на числовий тип для коректного сортування
    df['decade'] = pd.to_numeric(df['decade'], errors='coerce').fillna(0).astype(int)

    # Додаткова перевірка: чи містить колонка 'distributor' лише порожні рядки після очищення?
    if (df['distributor'] == '').all():
        print("Попередження: Колонка 'distributor' не містить значущих даних. Повертаю порожній DataFrame.")
        return pd.DataFrame(
            columns=['distributor', 'product_name', 'full_address', 'year', 'month', 'decade', 'actual_quantity', 'new_client'])

    # Крок 1: Агрегуємо quantity за всіма ключовими полями, включаючи дистриб'ютора, клієнта та декаду.
    # Оскільки 'quantity' тепер вважається кумулятивною, ми беремо МАКСИМУМ для кожної групи
    # (або останнє значення, якщо дані вже відсортовані за часом).
    # Це гарантує, що для кожної унікальної декади в групі ми отримуємо фінальне кумулятивне значення.
    aggregated_df = df.groupby(
        ['distributor', 'product_name', 'full_address', 'year', 'month', 'decade', 'new_client']
    )['quantity'].max().reset_index() # Змінено .sum() на .max()

    # Крок 2: Сортуємо дані для коректного обчислення "чистих" продажів.
    # Сортування за декадою є критично важливим.
    aggregated_df = aggregated_df.sort_values(
        by=['distributor', 'product_name', 'full_address', 'year', 'month', 'new_client', 'decade']
    )

    # Крок 3: Обчислюємо кумулятивну суму попередньої декади для віднімання.
    # Тепер 'quantity' сама по собі є кумулятивною сумою.
    # Ми просто беремо попереднє значення 'quantity' в межах групи.
    aggregated_df['prev_decade_quantity'] = aggregated_df.groupby(
        ['distributor', 'product_name', 'full_address', 'year', 'month', 'new_client']
    )['quantity'].shift(1).fillna(0)

    # Крок 4: Розраховуємо фактичні продажі за декаду.
    # Це буде 'quantity' поточної декади мінус 'quantity' попередньої декади.
    aggregated_df['actual_quantity'] = (
        aggregated_df['quantity'] - aggregated_df['prev_decade_quantity']
    )

    # Вибираємо та перейменовуємо потрібні колонки для фінального результату
    result = aggregated_df[[
        'distributor', 'product_name', 'full_address', 'year', 'month', 'decade', 'actual_quantity', 'new_client'
    ]]

    # Перетворюємо 'decade' назад у рядок, щоб відповідати очікуваному формату виводу.
    result['decade'] = result['decade'].astype(str)

    # Фільтруємо записи, де фактична кількість не дорівнює 0.
    return result[result['actual_quantity'] != 0]


# --- Решта ваших оригінальних функцій залишаються без змін ---

def calculate_forecast_with_bootstrap(df_for_current_month: pd.DataFrame, last_decade: int, year: int, month: int,
                                      n_iterations: int = 1000) -> dict:
    """
    Розраховує загальний прогноз та довірчий інтервал з використанням методу бутстрапу.
    """
    if df_for_current_month.empty or last_decade >= 30:
        return {}

    cal = Ukraine()

    try:
        start_date = date(year, month, 1)
        end_date_of_period = date(year, month, last_decade)
    except ValueError:
        return {}

    workdays_passed = 0
    current_day = start_date
    while current_day <= end_date_of_period:
        if cal.is_working_day(current_day):
            workdays_passed += 1
        current_day += timedelta(days=1)

    if workdays_passed <= 0:
        return {}

    if month == 12:
        first_day_of_next_month = date(year + 1, 1, 1)
    else:
        first_day_of_next_month = date(year, month + 1, 1)
    last_day_of_month = first_day_of_next_month - timedelta(days=1)

    workdays_left = 0
    if end_date_of_period < last_day_of_month:
        current_day = end_date_of_period + timedelta(days=1)
        while current_day <= last_day_of_month:
            if cal.is_working_day(current_day):
                workdays_left += 1
            current_day += timedelta(days=1)

    total_revenue_so_far = df_for_current_month['revenue'].sum()
    total_quantity_so_far = df_for_current_month['quantity'].sum()

    bootstrap_forecasts_revenue = []
    sales_data = df_for_current_month['revenue'].values
    n_sales = len(sales_data)

    if n_sales == 0:
        return {}

    for _ in range(n_iterations):
        indices = np.random.randint(0, n_sales, size=n_sales)
        bootstrap_sample = sales_data[indices]
        sample_revenue = bootstrap_sample.sum()
        sample_daily_revenue_rate = sample_revenue / workdays_passed
        forecast_r = sample_revenue + (workdays_left * sample_daily_revenue_rate)
        bootstrap_forecasts_revenue.append(forecast_r)

    conf_interval_revenue = (
        np.percentile(bootstrap_forecasts_revenue, 2.5),
        np.percentile(bootstrap_forecasts_revenue, 97.5)
    )

    return {
        "point_forecast_revenue": total_revenue_so_far + (workdays_left * (total_revenue_so_far / workdays_passed)),
        "conf_interval_revenue": conf_interval_revenue,
        "bootstrap_distribution_revenue": bootstrap_forecasts_revenue,
        # Додано для передачі в інші функції
        "workdays_passed": workdays_passed,
        "workdays_left": workdays_left
    }


def calculate_product_level_forecast(df_for_current_month: pd.DataFrame, workdays_passed: int,
                                     workdays_left: int) -> pd.DataFrame:
    """
    Розраховує точковий прогноз доходу та кількості для кожного продукту.
    """
    if df_for_current_month.empty or workdays_passed <= 0:
        return pd.DataFrame()

    # 1. Агрегуємо фактичні дані по кожному продукту
    product_summary = df_for_current_month.groupby('product_name').agg(
        quantity_so_far=('quantity', 'sum'),
        revenue_so_far=('revenue', 'sum')
    ).reset_index()

    # 2. Розраховуємо середньоденну "швидкість" продажів для кожного продукту
    product_summary['daily_quantity_rate'] = product_summary['quantity_so_far'] / workdays_passed
    product_summary['daily_revenue_rate'] = product_summary['revenue_so_far'] / workdays_passed

    # 3. Розраховуємо прогноз до кінця місяця для кожного продукту
    product_summary['forecast_quantity'] = product_summary['quantity_so_far'] + (
            product_summary['daily_quantity_rate'] * workdays_left)
    product_summary['forecast_revenue'] = product_summary['revenue_so_far'] + (
            product_summary['daily_revenue_rate'] * workdays_left)

    return product_summary.sort_values(by='forecast_revenue', ascending=False)


def create_address_client_map(df: pd.DataFrame) -> dict:
    """
    Створює словник, що співставляє повну адресу з відформатованим рядком імен клієнтів.
    """
    if 'full_address' not in df.columns or 'client' not in df.columns:
        return {}
    address_map = (
        df.groupby('full_address')['new_client']
        .unique()
        .apply(lambda x: ', '.join(sorted(x)))
        .to_dict()
    )
    return address_map


def calculate_main_kpis(df: pd.DataFrame) -> dict:
    """
    Розраховує ключові показники (KPI).
    """
    if df.empty:
        return {
            "total_quantity": 0, "unique_products": 0, "unique_clients": 0,
            "avg_quantity_per_client": 0, "top5_share": 0,
            "top_products": pd.Series(), "rev_top_products": pd.Series()
        }

    total_quantity = df['quantity'].sum()
    unique_products = df['product_name'].nunique()
    unique_clients = df.drop_duplicates(subset=['new_client', 'full_address']).shape[0]
    avg_quantity_per_client = total_quantity / unique_clients if unique_clients else 0
    product_sales = df.groupby('product_name')['quantity'].sum().sort_values(ascending=False)
    top5_total = product_sales.head(5).sum()
    top5_share = (top5_total / total_quantity * 100) if total_quantity else 0

    return {
        "total_quantity": total_quantity,
        "unique_products": unique_products,
        "unique_clients": unique_clients,
        "avg_quantity_per_client": avg_quantity_per_client,
        "top5_share": top5_share,
        "top_products": product_sales.head(5),
        "rev_top_products": product_sales.sort_values(ascending=True).head(5)
    }
