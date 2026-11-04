from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.product import Inventory


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_product_id(self, product_id: int) -> Optional[Inventory]:
        stmt = select(Inventory).where(Inventory.product_id == product_id)
        return self.db.scalars(stmt).first()

    def upsert_inventory(self, product_id: int, stock_quantity: int, reserved_quantity: int = 0) -> Inventory:
        existing = self.get_by_product_id(product_id)
        if existing:
            existing.stock_quantity = stock_quantity
            existing.reserved_quantity = reserved_quantity
            self.db.flush()
            return existing
        new_inv = Inventory(product_id=product_id, stock_quantity=stock_quantity, reserved_quantity=reserved_quantity)
        self.db.add(new_inv)
        self.db.flush()
        return new_inv

    def update_stock(self, product_id: int, quantity_delta: int) -> Optional[Inventory]:
        inv = self.get_by_product_id(product_id)
        if not inv:
            return None
        if inv.stock_quantity + quantity_delta < 0:
            raise ValueError(f"Insufficient stock for product {product_id}")
        inv.stock_quantity += quantity_delta
        self.db.flush()
        return inv
