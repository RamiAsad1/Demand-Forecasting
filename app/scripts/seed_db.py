"""
seed_db.py
----------
One-time script to:
  1. Create all database tables
  2. Load data from CSVs into the database
"""

import sys
from pathlib import Path

# Allow imports from repo root
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
from app.db.database import engine, SessionLocal, Base
from app.db import models


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def create_tables():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("  ✅ Tables created")


def clear_tables(db):
    print("Clearing existing data...")
    db.query(models.InventorySnapshot).delete()
    db.query(models.Sale).delete()
    db.query(models.Product).delete()
    db.commit()
    print("  ✅ Tables cleared")


def seed_products(db):
    print("Seeding products...")
    df = pd.read_csv(DATA_DIR / "products.csv")
    for _, row in df.iterrows():
        db.add(models.Product(
            product_id       = int(row["product_id"]),
            name             = row["name"],
            category         = row["category"],
            shelf_life_days  = int(row["shelf_life_days"]),
            avg_daily_demand = float(row["avg_daily_demand"]),
        ))
    db.commit()
    print(f"  ✅ {len(df)} products seeded")


def seed_sales(db):
    print("Seeding sales...")
    df = pd.read_csv(DATA_DIR / "sales.csv", parse_dates=["sale_date"])
    for _, row in df.iterrows():
        db.add(models.Sale(
            sale_id       = int(row["sale_id"]),
            product_id    = int(row["product_id"]),
            quantity_sold = int(row["quantity_sold"]),
            sale_date     = row["sale_date"].date(),
        ))
    db.commit()
    print(f"  ✅ {len(df)} sales rows seeded")


def seed_inventory(db):
    print("Seeding inventory snapshots...")
    df = pd.read_csv(DATA_DIR / "inventory.csv", parse_dates=["snapshot_date"])
    for _, row in df.iterrows():
        db.add(models.InventorySnapshot(
            snapshot_id   = int(row["snapshot_id"]),
            product_id    = int(row["product_id"]),
            current_stock = int(row["current_stock"]),
            snapshot_date = row["snapshot_date"].date(),
        ))
    db.commit()
    print(f"  ✅ {len(df)} inventory rows seeded")


if __name__ == "__main__":
    create_tables()
    db = SessionLocal()
    try:
        clear_tables(db)
        seed_products(db)
        seed_sales(db)
        seed_inventory(db)
        print("\n✅ Database seeded successfully.")
    finally:
        db.close()