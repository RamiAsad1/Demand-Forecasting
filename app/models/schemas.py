"""
schemas.py
----------------------------------------------
This defines the shape of the data for the API layer.
"""

from datetime import date
from typing import List, Literal
from pydantic import BaseModel, Field, model_validator


class ProductForecast(BaseModel):
    product_id: int
    name: str
    category: Literal["Perishable", "Refrigerated", "Household"]
    rolling_avg_7d: float
    reorder_horizon: int
    predicted_weekly_demand: float
    current_stock: int
    projected_stock: float
    at_risk: bool


class ForecastReport(BaseModel):
    forecast_date: str
    total_products: int
    at_risk_count: int
    products: list[ProductForecast]


class SaleRecordIn(BaseModel):
    product_id: int
    quantity_sold: int = Field(..., ge=0)
    sale_date: date


class InventoryRecordIn(BaseModel):
    product_id: int
    current_stock: int = Field(..., ge=0)
    snapshot_date: date


class BulkSaleRequest(BaseModel):
    records: List[SaleRecordIn] = Field(..., min_length=1)

    @model_validator(mode="after")
    def no_duplicate_pairs(self) -> "BulkSaleRequest":
        """Reject duplicate product_id + sale_date pairs within a single batch."""
        seen = set()
        for r in self.records:
            key = (r.product_id, r.sale_date)
            if key in seen:
                raise ValueError(
                    f"Duplicate (product_id={r.product_id}, sale_date={r.sale_date}) "
                    "in request body."
                )
            seen.add(key)
        return self


class BulkInventoryRequest(BaseModel):
    records: List[InventoryRecordIn] = Field(..., min_length=1)

    @model_validator(mode="after")
    def no_duplicate_pairs(self) -> "BulkInventoryRequest":
        """Reject duplicate product_id + snapshot_date pairs within a single batch."""
        seen = set()
        for r in self.records:
            key = (r.product_id, r.snapshot_date)
            if key in seen:
                raise ValueError(
                    f"Duplicate (product_id={r.product_id}, snapshot_date={r.snapshot_date}) "
                    "in request body."
                )
            seen.add(key)
        return self


class BulkIngestionResponse(BaseModel):
    inserted: int
    updated: int
    message: str
