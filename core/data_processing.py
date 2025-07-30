import pandas as pd
import numpy as np
from datetime import date, timedelta
from workalendar.europe import Ukraine  # Бібліотека для розрахунку робочих днів в Україні


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


def compute_actual_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Розраховує "чисті" продажі між декадами з виправленою логікою.
    """
    if df.empty or 'decade' not in df.columns:
        return pd.DataFrame(columns=['product_name', 'full_address', 'year', 'month', 'decade', 'actual_quantity'])

    df = create_full_address(df)
    df = df[df['full_address'] != '']
    group_agg = df.groupby(['product_name', 'full_address', 'year', 'month', 'decade'])['quantity'].sum().reset_index()
    pivot = group_agg.pivot_table(
        index=['product_name', 'full_address', 'year', 'month'],
        columns='decade',
        values='quantity',
        fill_value=0
    )
    fact_10 = pivot.get('10', 0)
    fact_20 = (pivot['20'] - pivot.get('10', 0)) if '20' in pivot.columns else 0
    if '30' in pivot.columns:
        base_for_30 = pivot.get('20', pivot.get('10', 0))
        fact_30 = pivot['30'] - base_for_30
    else:
        fact_30 = 0
    pivot['fact_10'] = fact_10
    pivot['fact_20'] = fact_20
    pivot['fact_30'] = fact_30
    result = pivot[['fact_10', 'fact_20', 'fact_30']].stack().reset_index()
    result.columns = ['product_name', 'full_address', 'year', 'month', 'decade', 'actual_quantity']
    result['decade'] = result['decade'].str.replace('fact_', '')
    return result[result['actual_quantity'] != 0]
