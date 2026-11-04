import json
from langchain_core.tools import tool

from backend.database.connection import get_db_session
from backend.services.cart_service import CartService


@tool
def add_to_cart(product_id: int, quantity: int = 1) -> str:
    """
    Add a product to the user's shopping cart after validating physical stock availability.

    Args:
        product_id: The integer ID of the product to add
        quantity: The quantity to add (defaults to 1)
    """
    try:
        with get_db_session() as db:
            service = CartService(db)
            res = service.add_to_cart(product_id=product_id, quantity=quantity)
            cart_data = res.cart.model_dump(mode="json") if res.cart else None
            return json.dumps({
                "success": res.success,
                "action": res.action,
                "message": res.message,
                "cart": cart_data,
            }, indent=2)
    except Exception as e:
        return f"Database error adding item to cart: {str(e)}"


@tool
def remove_from_cart(product_id: int) -> str:
    """
    Remove a product completely from the user's shopping cart.

    Args:
        product_id: The integer ID of the product to remove
    """
    try:
        with get_db_session() as db:
            service = CartService(db)
            res = service.remove_from_cart(product_id=product_id)
            cart_data = res.cart.model_dump(mode="json") if res.cart else None
            return json.dumps({
                "success": res.success,
                "action": res.action,
                "message": res.message,
                "cart": cart_data,
            }, indent=2)
    except Exception as e:
        return f"Database error removing item from cart: {str(e)}"


@tool
def update_cart_item(product_id: int, quantity: int) -> str:
    """
    Update the quantity of an existing item in the shopping cart. Setting quantity to 0 removes the item.

    Args:
        product_id: The integer ID of the product in the cart
        quantity: The new target quantity (integer >= 0)
    """
    try:
        with get_db_session() as db:
            service = CartService(db)
            res = service.update_cart_item(product_id=product_id, quantity=quantity)
            cart_data = res.cart.model_dump(mode="json") if res.cart else None
            return json.dumps({
                "success": res.success,
                "action": res.action,
                "message": res.message,
                "cart": cart_data,
            }, indent=2)
    except Exception as e:
        return f"Database error updating cart: {str(e)}"


@tool
def get_cart() -> str:
    """
    Retrieve current shopping cart contents, line item subtotals, and total price.
    """
    try:
        with get_db_session() as db:
            service = CartService(db)
            cart = service.get_cart()
            if not cart.items:
                return "Your shopping cart is currently empty."

            return json.dumps(cart.model_dump(mode="json"), indent=2)
    except Exception as e:
        return f"Database error retrieving cart: {str(e)}"


@tool
def clear_cart() -> str:
    """
    Remove all items and completely empty the user's shopping cart.
    """
    try:
        with get_db_session() as db:
            service = CartService(db)
            res = service.clear_cart()
            return json.dumps({
                "success": res.success,
                "action": res.action,
                "message": res.message,
            }, indent=2)
    except Exception as e:
        return f"Database error clearing cart: {str(e)}"


CART_TOOLS = [
    add_to_cart,
    remove_from_cart,
    update_cart_item,
    clear_cart,
    get_cart,
]

