# Grocery Demand Forecasting System

A decision-support backend that helps grocery store managers identify which products are likely to run out in the upcoming week — before it happens.

---

## The Problem

Grocery stores lose revenue and customer trust through two failure modes: overstocking perishables that expire unsold, and understocking fast-movers that leave shelves empty. Both stem from the same root cause — restocking decisions made on intuition rather than data.

This system addresses that by analysing historical sales patterns and current inventory levels to surface a weekly risk report: *which products need restocking, and how urgently?*

---

## How It Works

Each day's sales and inventory snapshots are ingested into a SQLite database. A feature pipeline computes rolling demand signals per product. A forecasting service projects the next 7 days of demand against current stock, and flags any product where projected stock hits zero.

The result is exposed as a REST API — a clean JSON report that a frontend, a notification system, or a store management tool can consume directly.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| ORM | SQLAlchemy |
| Database | SQLite (Postgres-ready) |
| Data Processing | pandas, numpy |
| Validation | Pydantic v2 |
| Language | Python 3.11 |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/forecast` | Full weekly risk report for all products |
| `GET` | `/forecast/at-risk` | Filtered report — at-risk products only |
| `POST` | `/sales` | Bulk-ingest daily sale records |
| `POST` | `/inventory` | Bulk-ingest daily inventory snapshots |
| `GET` | `/docs` | Auto-generated Swagger UI |

### Example response — `/forecast/at-risk`

```json
{
  "forecast_date": "2024-04-01",
  "total_products": 2,
  "at_risk_count": 2,
  "products": [
    {
      "product_id": 4,
      "name": "Lettuce",
      "category": "Perishable",
      "current_stock": 59,
      "rolling_avg_7d": 19.6,
      "predicted_weekly_demand": 137.0,
      "projected_stock": -78.0,
      "at_risk": true
    }
  ]
}
```

---

## Getting Started

```bash
# 1. Clone the repo and activate the virtual environment
git clone https://github.com/RamiAsad1/Demand-Forecasting.git
cd Demand-Frocasting
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate synthetic data and seed the database
python data/generate_data.py
python app/scripts/seed_db.py

# 4. Start the API
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

---

## Project Structure

```
app/
├── db/              # SQLAlchemy engine, session, ORM models
├── models/          # Pydantic schemas (API validation)
├── pipelines/       # Feature engineering (data → signals)
├── services/        # Business logic (forecasting, ingestion)
└── scripts/         # One-time setup scripts (DB seeding)

data/                # Synthetic data generator + CSV sources
notebooks/           # Exploratory analysis and model validation
```

---

## Forecasting Approach

The current model uses a 7-day rolling average as the demand proxy:

```
predicted_weekly_demand = rolling_avg_7d × 7
projected_stock         = current_stock − predicted_weekly_demand
at_risk                 = projected_stock ≤ 0
```

Validated against a held-out 7-day backtest window. Baseline MAPE: **12.42%**.

Highest-error products (Bananas at 30.5%, Lettuce at 25.5%) are the primary targets for model improvement in the next iteration.

---

## Roadmap

- [ ] Weighted rolling average / exponential smoothing to beat 12.42% MAPE baseline
- [ ] Shelf-life-aware risk scoring
- [ ] Edge case handling (new products, zero-sales history)
- [ ] PostgreSQL migration for deployed environments
- [ ] Minimal frontend dashboard
