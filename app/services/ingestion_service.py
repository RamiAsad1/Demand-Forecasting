"""
Ingestion service.py
-----------------------------
Contains all the ingestion logic: product ID validation, duplicate counting for the response,
and the upsert loops for both sales and inventory.
"""

from typing import List, Set

from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from fastapi import HTTPException

from app.db.models import Product, Sale, InventorySnapshot
from app.models.schemas import SaleRecordIn, InventoryRecordIn, BulkIngestionResponse


def _fetch_valid_product_ids(db: Session) -> Set[int]:
    rows = db.query(Product.product_id).all()
    return {row[0] for row in rows}


def _validate_product_ids(
    product_ids: List[int],
    valid_ids: Set[int],
) -> None:
    unknown = sorted(set(product_ids) - valid_ids)
    if unknown:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown product_id(s): {unknown}. "
                   "All product IDs must exist before ingesting records.",
        )


def _count_existing_sales(
    db: Session,
    records: List[SaleRecordIn],
) -> int:
    pairs = [(r.product_id, r.sale_date) for r in records]
    count = 0
    for product_id, sale_date in pairs:
        exists = (
            db.query(Sale.sale_id)
            .filter(Sale.product_id == product_id, Sale.sale_date == sale_date)
            .first()
        )
        if exists:
            count += 1
    return count


def _count_existing_snapshots(
    db: Session,
    records: List[InventoryRecordIn],
) -> int:
    pairs = [(r.product_id, r.snapshot_date) for r in records]
    count = 0
    for product_id, snapshot_date in pairs:
        exists = (
            db.query(InventorySnapshot.snapshot_id)
            .filter(
                InventorySnapshot.product_id == product_id,
                InventorySnapshot.snapshot_date == snapshot_date,
            )
            .first()
        )
        if exists:
            count += 1
    return count


def ingest_sales(
    db: Session,
    records: List[SaleRecordIn],
) -> BulkIngestionResponse:
    valid_ids = _fetch_valid_product_ids(db)
    _validate_product_ids([r.product_id for r in records], valid_ids)

    existing = _count_existing_sales(db, records)
    inserted = len(records) - existing
    updated = existing

    for record in records:
        stmt = (
            sqlite_insert(Sale)
            .values(
                product_id=record.product_id,
                quantity_sold=record.quantity_sold,
                sale_date=record.sale_date,
            )
            .on_conflict_do_update(
                # SQLite upsert: match on the unique pair
                index_elements=["product_id", "sale_date"],
                set_={"quantity_sold": record.quantity_sold},
            )
        )
        db.execute(stmt)

    db.commit()

    return BulkIngestionResponse(
        inserted=inserted,
        updated=updated,
        message=f"Batch complete. {inserted} new record(s) inserted, "
                f"{updated} existing record(s) overwritten.",
    )


def ingest_inventory(
    db: Session,
    records: List[InventoryRecordIn],
) -> BulkIngestionResponse:
    valid_ids = _fetch_valid_product_ids(db)
    _validate_product_ids([r.product_id for r in records], valid_ids)

    existing = _count_existing_snapshots(db, records)
    inserted = len(records) - existing
    updated = existing

    for record in records:
        stmt = (
            sqlite_insert(InventorySnapshot)
            .values(
                product_id=record.product_id,
                current_stock=record.current_stock,
                snapshot_date=record.snapshot_date,
            )
            .on_conflict_do_update(
                index_elements=["product_id", "snapshot_date"],
                set_={"current_stock": record.current_stock},
            )
        )
        db.execute(stmt)

    db.commit()

    return BulkIngestionResponse(
        inserted=inserted,
        updated=updated,
        message=f"Batch complete. {inserted} new record(s) inserted, "
                f"{updated} existing record(s) overwritten.",
    )
