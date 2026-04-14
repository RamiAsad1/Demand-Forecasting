# app/main.py

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.pipelines.feature_pipelines import build_features
from app.services.forecast_service import generate_forecast
from app.services.ingestion_service import ingest_sales, ingest_inventory
from app.models.schemas import (
    ForecastReport,
    BulkSaleRequest,
    BulkInventoryRequest,
    BulkIngestionResponse,
)

app = FastAPI(
    title="Grocery Demand Forecasting API",
    version="0.4.0",
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/forecast", response_model=ForecastReport)
def forecast(db: Session = Depends(get_db)):
    features = build_features(db)
    return generate_forecast(features)


@app.get("/forecast/at-risk", response_model=ForecastReport)
def forecast_at_risk(db: Session = Depends(get_db)):
    features = build_features(db)
    report = generate_forecast(features)
    report.products = [p for p in report.products if p.at_risk]
    report.total_products = len(report.products)
    return report


@app.post("/sales", response_model=BulkIngestionResponse, status_code=200)
def post_sales(payload: BulkSaleRequest, db: Session = Depends(get_db)):
    """
    Bulk-ingest daily sale records.

    - Validates all product_ids before writing anything.
    - Upserts on (product_id, sale_date): overwrites quantity_sold if the
      record already exists, inserts if it does not.
    - The entire batch is committed atomically.
    """
    return ingest_sales(db, payload.records)


@app.post("/inventory", response_model=BulkIngestionResponse, status_code=200)
def post_inventory(payload: BulkInventoryRequest, db: Session = Depends(get_db)):
    """
    Bulk-ingest daily inventory snapshots.

    - Validates all product_ids before writing anything.
    - Upserts on (product_id, snapshot_date): overwrites current_stock if the
      record already exists, inserts if it does not.
    - The entire batch is committed atomically.
    """
    return ingest_inventory(db, payload.records)