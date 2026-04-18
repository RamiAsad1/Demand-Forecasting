"""
generate_data.py
----------------
Generates synthetic grocery store data for the Demand Forecasting system.

Output files (written to /data/):
  - products.csv       → product catalog
  - sales.csv          → daily sales per product (90 days)
  - inventory.csv      → daily inventory snapshots (90 days)

Run once from the repo root:
  python data/generate_data.py
"""

import os
import numpy as np
import pandas as pd
from datetime import date, timedelta

# ─── Reproducibility ──────────────────────────────────────────────────────────
# Fix the seed so every run produces the same data.
# This is critical: if data changes every run, your notebook results become
# inconsistent and your forecasting experiments aren't comparable.
np.random.seed(42)

# ─── Config ───────────────────────────────────────────────────────────────────
START_DATE = date(2024, 1, 1)
NUM_DAYS = 90  # ~3 months of history
OUTPUT_DIR = "data"  # relative to repo root

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Product Catalog ──────────────────────────────────────────────────────────
# Each product has:
#   - A realistic avg_daily_demand (used to generate sales)
#   - A shelf_life_days (perishables are tighter)
#   - A category
#
# The avg_daily_demand values are intentionally varied across categories to
# reflect real SKU diversity: bananas move fast, bleach moves slowly.

PRODUCTS = [
    # Perishables (fruits & vegetables)
    {"product_id": 1, "name": "Bananas", "category": "Perishable", "shelf_life_days": 5, "avg_daily_demand": 40},
    {"product_id": 2, "name": "Apples", "category": "Perishable", "shelf_life_days": 7, "avg_daily_demand": 30},
    {"product_id": 3, "name": "Tomatoes", "category": "Perishable", "shelf_life_days": 4, "avg_daily_demand": 25},
    {"product_id": 4, "name": "Lettuce", "category": "Perishable", "shelf_life_days": 3, "avg_daily_demand": 15},
    {"product_id": 5, "name": "Carrots", "category": "Perishable", "shelf_life_days": 10, "avg_daily_demand": 20},
    # Refrigerated
    {"product_id": 6, "name": "Whole Milk", "category": "Refrigerated", "shelf_life_days": 7, "avg_daily_demand": 50},
    {"product_id": 7, "name": "Yogurt", "category": "Refrigerated", "shelf_life_days": 14, "avg_daily_demand": 20},
    {"product_id": 8, "name": "Butter", "category": "Refrigerated", "shelf_life_days": 30, "avg_daily_demand": 10},
    {"product_id": 9, "name": "Orange Juice", "category": "Refrigerated", "shelf_life_days": 14,
     "avg_daily_demand": 35},
    {"product_id": 10, "name": "Cheddar Cheese", "category": "Refrigerated", "shelf_life_days": 21,
     "avg_daily_demand": 12},
    # Household
    {"product_id": 11, "name": "Dish Soap", "category": "Household", "shelf_life_days": 730, "avg_daily_demand": 8},
    {"product_id": 12, "name": "Bleach", "category": "Household", "shelf_life_days": 365, "avg_daily_demand": 3},
    {"product_id": 13, "name": "Paper Towels", "category": "Household", "shelf_life_days": 730, "avg_daily_demand": 15},
    {"product_id": 14, "name": "Shampoo", "category": "Household", "shelf_life_days": 730, "avg_daily_demand": 6},
    {"product_id": 15, "name": "Toothpaste", "category": "Household", "shelf_life_days": 730, "avg_daily_demand": 9},
]

products_df = pd.DataFrame(PRODUCTS)

# ─── Date Range ───────────────────────────────────────────────────────────────
dates = [START_DATE + timedelta(days=i) for i in range(NUM_DAYS)]

# ─── Sales Generation ─────────────────────────────────────────────────────────
# For each product × day, we simulate quantity_sold with two effects:
#
#   1. Weekend boost: people shop more on Fri/Sat/Sun.
#      We multiply demand by a day-of-week factor.
#
#   2. Random noise: real demand is never perfectly stable.
#      We use a Poisson distribution because:
#        - It produces non-negative integers (you can't sell -3 bananas)
#        - It naturally models "count of events per time period"
#        - Its variance scales with its mean (high-demand products are noisier)
#
#   3. Zero-sale days: ~5% chance per product per day.
#      Simulates days where a product temporarily wasn't available or
#      simply had no buyers. Important to model because your forecaster
#      must handle zeros gracefully.

WEEKEND_BOOST = {0: 1.0,  # Monday
                 1: 1.0,  # Tuesday
                 2: 1.0,  # Wednesday
                 3: 1.1,  # Thursday
                 4: 1.3,  # Friday
                 5: 1.4,  # Saturday
                 6: 1.2}  # Sunday

ZERO_SALE_PROB = 0.05  # 5% chance of zero-sale day

sales_rows = []
sale_id = 1

for product in PRODUCTS:
    for d in dates:
        # Zero-sale day?
        if np.random.rand() < ZERO_SALE_PROB:
            qty = 0
        else:
            boost = WEEKEND_BOOST[d.weekday()]
            adjusted_mean = product["avg_daily_demand"] * boost
            qty = int(np.random.poisson(adjusted_mean))

        # We still record zero-sale days — omitting them would distort
        # rolling averages and make the data look artificially clean.
        sales_rows.append({
            "sale_id": sale_id,
            "product_id": product["product_id"],
            "quantity_sold": qty,
            "sale_date": d.isoformat(),
        })
        sale_id += 1

sales_df = pd.DataFrame(sales_rows)

# ─── Inventory Snapshot Generation ───────────────────────────────────────────
# We simulate inventory as:
#   starting_stock − cumulative_sales + restocks
#
# Restock logic:
#   When stock drops below a reorder_threshold, we restock up to max_stock.
#   Threshold is set based on shelf_life (perishables restock more frequently).
#
# This produces realistic depletion curves with periodic replenishments,
# which is exactly what the forecasting logic will need to reason about.

inventory_rows = []
snapshot_id = 1

for product in PRODUCTS:
    shelf_life = product["shelf_life_days"]
    avg_demand = product["avg_daily_demand"]

    # Stock sizing rules:
    #   max_stock      = enough for ~2× shelf life worth of demand
    #   reorder_point  = enough to cover 1 shelf-life worth of demand
    #   (capped to avoid absurdly large numbers for long-shelf-life items)
    max_stock = min(avg_demand * shelf_life * 2, avg_demand * 30)
    reorder_point = min(avg_demand * shelf_life, avg_demand * 14)

    current_stock = max_stock  # start fully stocked

    # Filter this product's sales once (efficiency)
    product_sales = sales_df[sales_df["product_id"] == product["product_id"]].copy()
    product_sales = product_sales.set_index("sale_date")["quantity_sold"].to_dict()

    for d in dates:
        date_str = d.isoformat()

        # Subtract today's sales from stock
        sold_today = product_sales.get(date_str, 0)
        current_stock = max(current_stock - sold_today, 0)  # floor at 0

        # Restock if below threshold (simulates manager placing an order)
        if current_stock <= reorder_point:
            current_stock = int(max_stock)

        inventory_rows.append({
            "snapshot_id": snapshot_id,
            "product_id": product["product_id"],
            "current_stock": current_stock,
            "snapshot_date": date_str,
        })
        snapshot_id += 1

inventory_df = pd.DataFrame(inventory_rows)

# ─── Write to CSV ─────────────────────────────────────────────────────────────
products_df.to_csv(os.path.join(OUTPUT_DIR, "products.csv"), index=False)
sales_df.to_csv(os.path.join(OUTPUT_DIR, "sales.csv"), index=False)
inventory_df.to_csv(os.path.join(OUTPUT_DIR, "inventory.csv"), index=False)

print("✅ Data generated successfully.")
print(f"   products.csv  → {len(products_df)} products")
print(f"   sales.csv     → {len(sales_df)} rows ({NUM_DAYS} days × {len(PRODUCTS)} products)")
print(f"   inventory.csv → {len(inventory_df)} rows ({NUM_DAYS} days × {len(PRODUCTS)} products)")
