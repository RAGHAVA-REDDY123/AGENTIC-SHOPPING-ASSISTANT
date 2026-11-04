from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.models.product import Cart, CartItem, Product


class CartRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_cart(self, customer_id: str = "dev_customer_001") -> Cart:
        cart = self.get_cart(customer_id)
        if not cart:
            cart = Cart(customer_id=customer_id)
            self.db.add(cart)
            self.db.flush()
            cart = self.get_cart(customer_id)
        return cart

    def get_cart(self, customer_id: str = "dev_customer_001") -> Optional[Cart]:
        stmt = (
            select(Cart)
            .options(joinedload(Cart.items).joinedload(CartItem.product).joinedload(Product.inventory))
            .where(Cart.customer_id == customer_id)
        )
        return self.db.scalars(stmt).unique().first()

    def get_cart_item(self, cart_id: int, product_id: int) -> Optional[CartItem]:
        stmt = (
            select(CartItem)
            .options(joinedload(CartItem.product))
            .where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        )
        return self.db.scalars(stmt).first()

    def add_item(self, cart_id: int, product_id: int, quantity: int = 1) -> CartItem:
        item = self.get_cart_item(cart_id, product_id)
        if item:
            item.quantity += quantity
        else:
            item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
            self.db.add(item)
        self.db.flush()
        return item

    def update_item_quantity(self, cart_id: int, product_id: int, quantity: int) -> Optional[CartItem]:
        item = self.get_cart_item(cart_id, product_id)
        if not item:
            return None
        if quantity <= 0:
            self.db.delete(item)
            self.db.flush()
            return None
        item.quantity = quantity
        self.db.flush()
        return item

    def remove_item(self, cart_id: int, product_id: int) -> bool:
        item = self.get_cart_item(cart_id, product_id)
        if not item:
            return False
        self.db.delete(item)
        self.db.flush()
        return True
