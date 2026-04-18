"""
models.py
---------
SQLAlchemy ORM models — one class per database table.
Do not confuse with app/models/schemas.py which are API layer representations.
"""

from sqlalchemy import Column, Integer, Float, Text, Date, UniqueConstraint
from app.db.database import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    shelf_life_days = Column(Integer, nullable=False)
    avg_daily_demand = Column(Float, nullable=False)


class Sale(Base):
    __tablename__ = "sales"

    sale_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    quantity_sold = Column(Integer, nullable=False)
    sale_date = Column(Date, nullable=False,  index=True)
    __table_args__ = (
        UniqueConstraint("product_id", "sale_date", name="uq_sale_product_date"),
    )


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"

    snapshot_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    current_stock = Column(Integer, nullable=False)
    snapshot_date = Column(Date, nullable=False,  index=True)
    __table_args__ = (
        UniqueConstraint("product_id", "snapshot_date", name="uq_snapshot_product_date"),
    )
