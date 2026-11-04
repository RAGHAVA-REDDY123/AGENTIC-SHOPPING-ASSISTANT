from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from backend.repositories.cart_repository import CartRepository
from backend.repositories.product_repository import ProductRepository
from backend.services.inventory_service import InventoryService
from backend.schemas.product import CartActionResponse, CartItemRead, CartRead
import os

class CartService:

    def __init__(self, db: Session):
        self.db = db
        self.cart_repo = CartRepository(db)
        self.product_repo = ProductRepository(db)
        self.inventory_service = InventoryService(db)

    def _format_cart(self, customer_id: str) -> CartRead:
        cart = self.cart_repo.get_or_create_cart(customer_id)
        items_read = []
        total_items = 0
        total_price = Decimal("0.00")

        for item in cart.items:
            product = item.product
            subtotal = product.price * Decimal(item.quantity)
            total_items += item.quantity
            total_price += subtotal
            items_read.append(
                CartItemRead(
                    id=item.id,
                    product_id=product.id,
                    product_name=product.name,
                    product_slug=product.slug,
                    brand=product.brand,
                    unit_price=product.price,
                    quantity=item.quantity,
                    subtotal=subtotal,
                    image_url=product.image_url,
                )
            )

        return CartRead(
            id=cart.id,
            customer_id=cart.customer_id,
            items=items_read,
            total_items=total_items,
            total_price=total_price,
            updated_at=cart.updated_at,
        )

    def get_cart(self, customer_id: Optional[str] = None) -> CartRead:
        cid = customer_id or os.getenv("DEV_CUSTOMER_ID")
        return self._format_cart(cid)

    def add_to_cart(self, product_id: int, quantity: int = 1, customer_id: Optional[str] = None) -> CartActionResponse:

        cid = customer_id or os.getenv("DEV_CUSTOMER_ID")

        if quantity <= 0:
            return CartActionResponse(
                success=False,
                action="add_to_cart",
                message=f"Quantity must be a positive integer, got {quantity}.",
                cart=self._format_cart(cid),
            )

        # 1. Validate product existence
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return CartActionResponse(
                success=False,
                action="add_to_cart",
                message=f"Product with ID {product_id} does not exist in catalog.",
                cart=self._format_cart(cid),
            )

        # 2. Check current cart quantity plus requested addition against stock
        cart = self.cart_repo.get_or_create_cart(cid)
        existing_item = self.cart_repo.get_cart_item(cart.id, product_id)
        current_cart_qty = existing_item.quantity if existing_item else 0
        total_requested = current_cart_qty + quantity

        stock_check = self.inventory_service.check_availability(product_id, total_requested)
        if not stock_check.is_available:
            return CartActionResponse(
                success=False,
                action="add_to_cart",
                message=f"Cannot add {quantity} item(s): {stock_check.message}",
                cart=self._format_cart(cid),
            )

        # 3. Add item inside transaction
        self.cart_repo.add_item(cart.id, product_id, quantity)
        self.db.commit()

        updated_cart = self._format_cart(cid)
        return CartActionResponse(
            success=True,
            action="add_to_cart",
            message=f"Added {quantity} unit(s) of '{product.name}' to cart successfully.",
            cart=updated_cart,
        )

    def update_cart_item(self, product_id: int, quantity: int, customer_id: Optional[str] = None) -> CartActionResponse:

        cid = customer_id or os.getenv("DEV_CUSTOMER_ID")
        cart = self.cart_repo.get_or_create_cart(cid)

        existing_item = self.cart_repo.get_cart_item(cart.id, product_id)
        if not existing_item:
            return CartActionResponse(
                success=False,
                action="update_cart_item",
                message=f"Product ID {product_id} is not in the cart.",
                cart=self._format_cart(cid),
            )

        if quantity <= 0:
            # Remove item
            self.cart_repo.remove_item(cart.id, product_id)
            self.db.commit()
            return CartActionResponse(
                success=True,
                action="remove_from_cart",
                message=f"Removed '{existing_item.product.name}' from cart.",
                cart=self._format_cart(cid),
            )

        # Verify stock for the new target quantity
        stock_check = self.inventory_service.check_availability(product_id, quantity)
        if not stock_check.is_available:
            return CartActionResponse(
                success=False,
                action="update_cart_item",
                message=f"Cannot update quantity to {quantity}: {stock_check.message}",
                cart=self._format_cart(cid),
            )

        self.cart_repo.update_item_quantity(cart.id, product_id, quantity)
        self.db.commit()

        return CartActionResponse(
            success=True,
            action="update_cart_item",
            message=f"Updated quantity of '{existing_item.product.name}' to {quantity}.",
            cart=self._format_cart(cid),
        )

    def remove_from_cart(self, product_id: int, customer_id: Optional[str] = None) -> CartActionResponse:
        cid = customer_id or os.getenv("DEV_CUSTOMER_ID")
        cart = self.cart_repo.get_or_create_cart(cid)

        existing_item = self.cart_repo.get_cart_item(cart.id, product_id)
        if not existing_item:
            return CartActionResponse(
                success=False,
                action="remove_from_cart",
                message=f"Product ID {product_id} is not present in your cart.",
                cart=self._format_cart(cid),
            )

        product_name = existing_item.product.name
        self.cart_repo.remove_item(cart.id, product_id)
        self.db.commit()

        return CartActionResponse(
            success=True,
            action="remove_from_cart",
            message=f"Successfully removed '{product_name}' from your cart.",
            cart=self._format_cart(cid),
        )

    def clear_cart(self, customer_id: Optional[str] = None) -> CartActionResponse:
        cid = customer_id or os.getenv("DEV_CUSTOMER_ID")
        cart = self.cart_repo.get_or_create_cart(cid)
        for item in list(cart.items):
            self.cart_repo.remove_item(cart.id, item.product_id)
        self.db.commit()
        return CartActionResponse(
            success=True,
            action="clear_cart",
            message="Your shopping cart has been cleared successfully.",
            cart=self._format_cart(cid),
        )   