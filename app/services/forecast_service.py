"""
forecast_service.py
-------------------
Produces a weekly restock risk report from an enriched feature DataFrame.
This is the production equivalent of forecasting.ipynb.
"""

import pandas as pd
from datetime import date
from app.models.schemas import ForecastReport, ProductForecast


def generate_forecast(df: pd.DataFrame) -> ForecastReport:
    # Isolate most recent row per product
    latest = (
        df.sort_values("sale_date")
        .groupby("product_id")
        .last()
        .reset_index()
    )

    # Baseline forecast: rolling avg × 7
    latest["predicted_weekly_demand"] = (latest["rolling_avg_7d"] * 7).round(1)
    latest["projected_stock"] = (
            latest["current_stock"] - latest["predicted_weekly_demand"]
    ).round(1)
    latest["at_risk"] = latest["projected_stock"] <= 0

    # Build list of Pydantic models
    products = [
        ProductForecast(
            product_id=int(row["product_id"]),
            name=row["name"],
            category=row["category"],
            current_stock=int(row["current_stock"]),
            rolling_avg_7d=float(row["rolling_avg_7d"]),
            predicted_weekly_demand=float(row["predicted_weekly_demand"]),
            projected_stock=float(row["projected_stock"]),
            at_risk=bool(row["at_risk"]),
        )
        for _, row in latest.iterrows()
    ]

    return ForecastReport(
        forecast_date=date.today().isoformat(),
        total_products=len(products),
        at_risk_count=sum(p.at_risk for p in products),
        products=products,
    )
