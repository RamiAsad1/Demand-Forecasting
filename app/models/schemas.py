"""
schemas.py
----------------------------------------------
This defines the shape of the data for the API layer.
"""

from pydantic import BaseModel
from typing import Literal


class ProductForecast(BaseModel):
    product_id: int
    name: str
    category: Literal["Perishable", "Refrigerated", "Household"]
    rolling_avg_7d: float
    predicted_weekly_demand: float
    current_stock: int
    projected_stock: float
    at_risk: bool


class ForecastReport(BaseModel):
    forecast_date: str
    total_products: int
    at_risk_count: int
    products: list[ProductForecast]
