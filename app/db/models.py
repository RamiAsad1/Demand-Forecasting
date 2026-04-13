"""
models.py
---------
SQLAlchemy ORM models — one class per database table.
Do not confuse with app/models/schemas.py which are API layer representations.
"""

from sqlalchemy import Column, Integer, String, Float, Date
from app.db.database import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    shelf_life_days = Column(Integer, nullable=False)
    avg_daily_demand = Column(Float, nullable=False)


class Sale(Base):
    __tablename__ = "sales"

    sale_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    quantity_sold = Column(Integer, nullable=False)
    sale_date = Column(Date, nullable=False,  index=True)


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"

    snapshot_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    current_stock = Column(Integer, nullable=False)
    snapshot_date = Column(Date, nullable=False,  index=True)