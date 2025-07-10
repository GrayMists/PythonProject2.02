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
    unique_clients = df['full_address'].nunique()
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
    Розраховує "чисті" продажі між декадами.
    Це складна логіка, яка тепер ізольована в одній функції.
    """
    if df.empty or 'decade' not in df.columns:
        return pd.DataFrame(columns=['product_name', 'full_address', 'year', 'month', 'decade', 'actual_quantity'])

    # Переконуємось, що адреса існує
    df = create_full_address(df)
    df = df[df['full_address'] != '']

    # Агрегуємо, щоб уникнути дублікатів перед розрахунком
    group_agg = df.groupby(['product_name', 'full_address', 'year', 'month', 'decade'])['quantity'].sum().reset_index()

    pivot = group_agg.pivot_table(
        index=['product_name', 'full_address', 'year', 'month'],
        columns='decade',
        values='quantity',
        fill_value=0
    )

    # Розрахунок "чистих" продажів
    pivot['fact_30'] = pivot.get('30', 0) - pivot.get('20', 0)
    pivot['fact_20'] = pivot.get('20', 0) - pivot.get('10', 0)
    pivot['fact_10'] = pivot.get('10', 0)

    result = pivot[['fact_10', 'fact_20', 'fact_30']].stack().reset_index()
    result.columns = ['product_name', 'full_address', 'year', 'month', 'decade', 'actual_quantity']
    result['decade'] = result['decade'].str.replace('fact_', '')

    # Повертаємо тільки ті рядки, де були фактичні продажі
    return result[result['actual_quantity'] > 0]
