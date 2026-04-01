"""
feature_pipelines.py
-------------------
Loads raw CSVs and produces an enriched feature DataFrame.
This is the production equivalent of feature_engineering.ipynb.
"""

import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_raw_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    products = pd.read_csv(DATA_DIR / "products.csv")
    sales = pd.read_csv(DATA_DIR / "sales.csv", parse_dates=["sale_date"])
    inventory = pd.read_csv(DATA_DIR / "inventory.csv", parse_dates=["snapshot_date"])
    return products, sales, inventory


def build_features() -> pd.DataFrame:
    products, sales, inventory = load_raw_data()

    # Merge into one DataFrame
    df = (
        sales
        .merge(products[["product_id", "name", "category", "shelf_life_days"]],
               on="product_id")
        .merge(inventory[["product_id", "snapshot_date", "current_stock"]],
               left_on=["product_id", "sale_date"],
               right_on=["product_id", "snapshot_date"])
        .drop(columns=["snapshot_date"])
        .sort_values(["product_id", "sale_date"])
        .reset_index(drop=True)
    )

    # Rolling demand features (grouped per product)
    grp = df.groupby("product_id")["quantity_sold"]

    df["rolling_avg_7d"] = grp.transform(
        lambda x: x.rolling(7, min_periods=1).mean()).round(2)
    df["rolling_avg_14d"] = grp.transform(
        lambda x: x.rolling(14, min_periods=1).mean()).round(2)
    df["rolling_std_7d"] = grp.transform(
        lambda x: x.rolling(7, min_periods=1).std()).round(2).fillna(0)
    df["weekly_total"] = grp.transform(
        lambda x: x.rolling(7, min_periods=1).sum()).astype(int)

    df["day_of_week"] = df["sale_date"].dt.day_of_week

    df["days_until_stockout"] = (
            df["current_stock"] / df["rolling_avg_7d"].replace(0, np.nan)
    ).fillna(999).clip(upper=999).round(1)

    return df
