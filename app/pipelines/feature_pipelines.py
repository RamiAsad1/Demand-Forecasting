"""
feature_pipelines.py
-------------------
Loads data from the database and produces an enriched feature DataFrame.
Updated to use SQLAlchemy session instead of raw CSVs.
"""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import models


def load_raw_data(db: Session) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Query all products, sales, and inventory from the database."""

    products = pd.DataFrame([{
        "product_id": p.product_id,
        "name": p.name,
        "category": p.category,
        "shelf_life_days": p.shelf_life_days,
    } for p in db.query(models.Product).all()])

    sales = pd.DataFrame([{
        "sale_id": s.sale_id,
        "product_id": s.product_id,
        "quantity_sold": s.quantity_sold,
        "sale_date": pd.Timestamp(s.sale_date),
    } for s in db.query(models.Sale).all()])

    inventory = pd.DataFrame([{
        "snapshot_id": i.snapshot_id,
        "product_id": i.product_id,
        "current_stock": i.current_stock,
        "snapshot_date": pd.Timestamp(i.snapshot_date),
    } for i in db.query(models.InventorySnapshot).all()])

    return products, sales, inventory


def build_features(db: Session = None) -> pd.DataFrame:
    """
    Merge raw data and compute rolling demand features.
    Accepts an optional db session — creates one internally if not provided.
    """
    if db is None:
        db = SessionLocal()

    products, sales, inventory = load_raw_data(db)

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

    grp = df.groupby("product_id")["quantity_sold"]

    df["rolling_avg_7d"] = grp.transform(
        lambda x: x.rolling(7, min_periods=1).mean()).round(2)
    df["rolling_avg_14d"] = grp.transform(
        lambda x: x.rolling(14, min_periods=1).mean()).round(2)
    df["rolling_std_7d"] = grp.transform(
        lambda x: x.rolling(7, min_periods=1).std()).round(2).fillna(0)
    df["weekly_total"] = grp.transform(
        lambda x: x.rolling(7, min_periods=1).sum()).astype(int)

    df["day_of_week"] = df["sale_date"].dt.dayofweek

    df["days_until_stockout"] = (
            df["current_stock"] / df["rolling_avg_7d"].replace(0, np.nan)
    ).fillna(999).clip(upper=999).round(1)

    return df
