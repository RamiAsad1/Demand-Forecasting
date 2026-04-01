"""
main.py
-------
FastAPI application entry point.
Exposes the demand forecasting API.
"""

from fastapi import FastAPI, HTTPException
from app.pipelines.feature_pipelines import build_features
from app.services.forecast_service import generate_forecast
from app.models.schemas import ForecastReport

app = FastAPI(
    title="Demand Forecasting API",
    description="Predicts which grocery products are at risk of stockout in the next 7 days.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """Confirm that the API is running."""
    return {"status": "ok"}


@app.get("/forecast", response_model=ForecastReport)
def get_forecast():
    """
    Returns a full weekly restock risk report.
    Flags products whose projected stock after 7 days is <= 0.
    """
    try:
        df = build_features()
        report = generate_forecast(df)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/forecast/at-risk", response_model=ForecastReport)
def get_at_risk_only():
    """
    Returns only the products at risk of stockout.
    Filtered subset of /forecast.
    """
    try:
        df = build_features()
        report = generate_forecast(df)
        at_risk = [p for p in report.products if p.at_risk]
        return ForecastReport(
            forecast_date=report.forecast_date,
            total_products=report.total_products,
            at_risk_count=report.at_risk_count,
            products=at_risk,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
