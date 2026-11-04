from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from backend.repositories.inventory_repository import InventoryRepository
from backend.repositories.product_repository import ProductRepository
from backend.schemas.product import InventoryCheckResult


class InventoryService:
    
    def __init__(self, db: Session):
        self.db = db
        self.inventory_repo = InventoryRepository(db)
        self.product_repo = ProductRepository(db)

    def check_availability(self, product_id: int, requested_quantity: int = 1) -> InventoryCheckResult:
        if requested_quantity <= 0:
            return InventoryCheckResult(
                product_id=product_id,
                product_name="Unknown",
                is_available=False,
                stock_quantity=0,
                requested_quantity=requested_quantity,
                status="invalid_quantity",
                message=f"Requested quantity must be at least 1, received: {requested_quantity}",
            )

        product = self.product_repo.get_by_id(product_id)
        if not product:
            return InventoryCheckResult(
                product_id=product_id,
                product_name="Not Found",
                is_available=False,
                stock_quantity=0,
                requested_quantity=requested_quantity,
                status="product_not_found",
                message=f"Product with ID {product_id} does not exist in the catalog.",
            )

        inv = self.inventory_repo.get_by_product_id(product_id)
        available_stock = (inv.stock_quantity - inv.reserved_quantity) if inv else 0
        if available_stock < 0:
            available_stock = 0

        if available_stock == 0:
            return InventoryCheckResult(
                product_id=product.id,
                product_name=product.name,
                is_available=False,
                stock_quantity=0,
                requested_quantity=requested_quantity,
                status="out_of_stock",
                message=f"'{product.name}' is currently out of stock.",
            )

        if available_stock < requested_quantity:
            return InventoryCheckResult(
                product_id=product.id,
                product_name=product.name,
                is_available=False,
                stock_quantity=available_stock,
                requested_quantity=requested_quantity,
                status="insufficient_quantity",
                message=f"Only {available_stock} unit(s) available for '{product.name}', but {requested_quantity} requested.",
            )

        status = "low_stock" if available_stock <= 3 else "in_stock"
        return InventoryCheckResult(
            product_id=product.id,
            product_name=product.name,
            is_available=True,
            stock_quantity=available_stock,
            requested_quantity=requested_quantity,
            status=status,
            message=f"'{product.name}' is in stock ({available_stock} available).",
        )

    def check_multiple(self, product_ids: List[int]) -> Dict[int, InventoryCheckResult]:
        """Check availability for multiple product IDs."""
        return {pid: self.check_availability(pid, 1) for pid in product_ids}
