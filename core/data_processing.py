import pandas as pd


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
    Наприклад: {'м. Київ, вул. Хрещатик, 1': 'Аптека-1, Аптека-2'}
    """
    if 'full_address' not in df.columns or 'client' not in df.columns:
        return {}

    # Групуємо по адресі, збираємо унікальні імена клієнтів, сортуємо та об'єднуємо в рядок
    address_map = (
        df.groupby('full_address')['client']
        .unique()
        .apply(lambda x: ', '.join(sorted(x)))
        .to_dict()
    )
    return address_map


def calculate_main_kpis(df: pd.DataFrame) -> dict:
    """
    Розраховує ключові показники (KPI).
    Приймає DataFrame, повертає словник. Не використовує Streamlit.
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
        "unique_clients": unique_clients,  # Тепер цей ключ містить потрібну вам цифру
        "avg_quantity_per_client": avg_quantity_per_client,
        "top5_share": top5_share,
        "top_products": product_sales.head(5),
        "rev_top_products": product_sales.sort_values(ascending=True).head(5)
    }


def compute_actual_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Розраховує "чисті" продажі між декадами з виправленою логікою.
    """
    # ### ЗМІНЕНО ###: Додано 'new_client' до перевірки та до повернення порожнього DF
    required_cols = ['new_client', 'product_name', 'full_address', 'year', 'month', 'decade', 'quantity']
    if df.empty or not all(col in df.columns for col in required_cols):
        return pd.DataFrame(columns=['new_client', 'product_name', 'full_address', 'year', 'month', 'decade', 'actual_quantity'])

    df = create_full_address(df)
    df = df[df['full_address'] != '']

    # ### ЗМІНЕНО ###: Додаємо 'new_client' до групування, щоб не втратити його
    group_agg = df.groupby(['new_client', 'product_name', 'full_address', 'year', 'month', 'decade'])['quantity'].sum().reset_index()

    # ### ЗМІНЕНО ###: Додаємо 'new_client' до індексу зведеної таблиці
    pivot = group_agg.pivot_table(
        index=['new_client', 'product_name', 'full_address', 'year', 'month'],
        columns='decade',
        values='quantity',
        fill_value=0
    )

    # --- ВИПРАВЛЕНА ЛОГІКА РОЗРАХУНКУ ФАКТИЧНИХ ПРОДАЖІВ ---

    # Фактичні продажі за 10-ту декаду - це просто сума на 10-ту декаду
    fact_10 = pivot.get('10', 0)

    # Фактичні продажі за 20-ту декаду розраховуються, тільки якщо колонка '20' існує
    fact_20 = (pivot['20'] - pivot.get('10', 0)) if '20' in pivot.columns else 0

    # Фактичні продажі за 30-ту декаду розраховуються, тільки якщо колонка '30' існує
    if '30' in pivot.columns:
        # Базою для віднімання є остання існуюча декада (20 або 10)
        base_for_30 = pivot.get('20', pivot.get('10', 0))
        fact_30 = pivot['30'] - base_for_30
    else:
        fact_30 = 0

    pivot['fact_10'] = fact_10
    pivot['fact_20'] = fact_20
    pivot['fact_30'] = fact_30

    result = pivot[['fact_10', 'fact_20', 'fact_30']].stack().reset_index()
    result.columns = ['new_client', 'product_name', 'full_address', 'year', 'month', 'decade', 'actual_quantity']
    result['decade'] = result['decade'].str.replace('fact_', '')

    # Повертаємо тільки ті рядки, де були фактичні продажі (додатні або від'ємні)
    return result[result['actual_quantity'] != 0]
