"""Core data processing utilities."""

from __future__ import annotations

import pandas as pd

from .text_cleaning import create_full_address


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
    required_cols = [
        "decade",
        "distributor",
        "product_name",
        "quantity",
        "year",
        "month",
        "city",
        "street",
        "house_number",
        "new_client",
    ]
    for col in required_cols:
        if col not in df.columns:
            print(
                f"Попередження: Відсутня необхідна колонка '{col}'. Повертаю порожній DataFrame."
            )
            return pd.DataFrame(
                columns=[
                    "distributor",
                    "product_name",
                    "full_address",
                    "year",
                    "month",
                    "decade",
                    "actual_quantity",
                    "new_client",
                ]
            )

    if df.empty:
        print("Попередження: Вхідний DataFrame порожній. Повертаю порожній DataFrame.")
        return pd.DataFrame(
            columns=[
                "distributor",
                "product_name",
                "full_address",
                "year",
                "month",
                "decade",
                "actual_quantity",
                "new_client",
            ]
        )

    # --- КРОК ОЧИЩЕННЯ ДАНИХ ---
    # Примусово видаляємо зайві пробіли з ключових текстових полів.
    text_cols_to_clean = [
        "distributor",
        "product_name",
        "city",
        "street",
        "house_number",
        "new_client",
    ]
    for col in text_cols_to_clean:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    # Створення повної адреси відбувається ПІСЛЯ очищення її компонентів
    df = create_full_address(df)
    df = df[df["full_address"] != ""]
    # Перетворюємо 'decade' на числовий тип для коректного сортування
    df["decade"] = pd.to_numeric(df["decade"], errors="coerce").fillna(0).astype(int)

    # Додаткова перевірка: чи містить колонка 'distributor' лише порожні рядки після очищення?
    if (df["distributor"] == "").all():
        print(
            "Попередження: Колонка 'distributor' не містить значущих даних. Повертаю порожній DataFrame."
        )
        return pd.DataFrame(
            columns=[
                "distributor",
                "product_name",
                "full_address",
                "year",
                "month",
                "decade",
                "actual_quantity",
                "new_client",
            ]
        )

    # КРОК: Агрегуємо продажі в межах декади (сума всіх замовлень в декаді)
    df = df.groupby(
        [
            "distributor",
            "product_name",
            "full_address",
            "year",
            "month",
            "decade",
            "new_client",
        ],
        as_index=False,
    )["quantity"].sum()

    # Тепер aggregated_df — це просто df після агрегації
    aggregated_df = df

    # Крок 2: Сортуємо дані для коректного обчислення "чистих" продажів.
    aggregated_df = aggregated_df.sort_values(
        by=[
            "distributor",
            "product_name",
            "full_address",
            "year",
            "month",
            "new_client",
            "decade",
        ]
    )

    # Крок 3: Обчислюємо кумулятивну суму попередньої декади для віднімання.
    aggregated_df["prev_decade_quantity"] = (
        aggregated_df.groupby(
            [
                "distributor",
                "product_name",
                "full_address",
                "year",
                "month",
                "new_client",
            ]
        )["quantity"]
        .shift(1)
        .fillna(0)
    )

    # Крок 4: Розраховуємо фактичні продажі за декаду.
    aggregated_df["actual_quantity"] = (
        aggregated_df["quantity"] - aggregated_df["prev_decade_quantity"]
    )

    # Вибираємо та перейменовуємо потрібні колонки для фінального результату
    result = aggregated_df[
        [
            "distributor",
            "product_name",
            "full_address",
            "year",
            "month",
            "decade",
            "actual_quantity",
            "new_client",
        ]
    ]

    # Перетворюємо 'decade' назад у рядок, щоб відповідати очікуваному формату виводу.
    result["decade"] = result["decade"].astype(str)

    # Фільтруємо записи, де фактична кількість не дорівнює 0.
    return result[result["actual_quantity"] != 0]


def compute_main_kpis(df: pd.DataFrame) -> dict[str, float]:
    """Compute basic KPIs for the sales dataset."""
    if df.empty:
        return {"total_quantity": 0.0, "unique_clients": 0, "unique_products": 0}
    return {
        "total_quantity": float(df["actual_quantity"].sum()),
        "unique_clients": int(df["full_address"].nunique()),
        "unique_products": int(df["product_name"].nunique()),
    }
