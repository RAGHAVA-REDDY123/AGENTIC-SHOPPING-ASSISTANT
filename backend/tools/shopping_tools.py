import json
from decimal import Decimal
from typing import Optional
from langchain_core.tools import tool

from backend.database.connection import get_db_session
from backend.services.cart_service import CartService
from backend.services.inventory_service import InventoryService
from backend.services.product_service import ProductService


@tool
def search_products(
    query: Optional[str] = None,
    category_slug: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    target_budget: Optional[float] = None,
    limit: int = 5,
) -> str:
    """
    Search products in the catalog.
    
    Args:
        query: Short keywords only (e.g. 'gaming', 'lightweight'). Do NOT include prices, questions, or 'find/show'.
        category_slug: Optional category slug (e.g. 'laptops', 'mobiles', 'headphones', 'accessories').
        brand: Optional brand name (e.g. 'Apple', 'ASUS', 'Dell').
        min_price: Optional minimum price in INR.
        max_price: Optional maximum price in INR (e.g. 100000).
        min_rating: Optional minimum customer rating (e.g. 4.0).
        target_budget: Optional spending target in INR.
        limit: Number of items to return (default 5).
    """
    try:
        with get_db_session() as db:
            service = ProductService(db)
            min_p = Decimal(str(min_price)) if min_price is not None else None
            max_p = Decimal(str(max_price)) if max_price is not None else None
            min_r = Decimal(str(min_rating)) if min_rating is not None else None
            budget = Decimal(str(target_budget)) if target_budget is not None else None

            results = service.search_products(
                query=query,
                category_slug=category_slug,
                brand=brand,
                min_price=min_p,
                max_price=max_p,
                min_rating=min_r,
                target_budget=budget,
                apply_ranking=True,
                limit=min(limit, 20),
            )

            if not results:
                return "No products matched your search criteria."

            formatted = []
            for p in results:
                stock_qty = p.get("stock_quantity", 0)
                if not p.get("in_stock", False) or stock_qty <= 0:
                    stock_status = "out_of_stock"
                elif stock_qty <= 3:
                    stock_status = f"low_stock (Only {stock_qty} left)"
                else:
                    stock_status = "in_stock"

                formatted.append({
                    "id": p["id"],
                    "name": p["name"],
                    "slug": p["slug"],
                    "brand": p["brand"],
                    "category": p["category_slug"],
                    "price": f"₹{p['price']:,.2f}",
                    "original_price": f"₹{p['original_price']:,.2f}",
                    "discount": f"{p['discount_percent']}%",
                    "rating": f"{p['rating']}/5.0 ({p['review_count']} reviews)",
                    "stock_status": stock_status,
                    "ranking_score": p["ranking_score"],
                    "ranking_criteria": p["ranking_criteria"],
                    "key_features": p["features"],
                })

            return json.dumps(formatted, indent=2)
    except Exception as e:
        return f"Database error during product search: {str(e)}"


@tool
def get_product_details(identifier: str) -> str:
    """Retrieve detailed specifications, features, and inventory for a product ID or slug."""
    try:
        with get_db_session() as db:
            service = ProductService(db)
            details = service.get_product_details(identifier)
            if not details:
                return f"Product '{identifier}' was not found in the catalog."

            stock_qty = details.get("stock_quantity", 0)
            if not details.get("in_stock", False) or stock_qty <= 0:
                stock_status = "out_of_stock"
            elif stock_qty <= 3:
                stock_status = f"low_stock (Only {stock_qty} left)"
            else:
                stock_status = "in_stock"

            formatted = {
                "id": details["id"],
                "name": details["name"],
                "slug": details["slug"],
                "description": details["description"],
                "brand": details["brand"],
                "category": details["category_slug"],
                "price": f"₹{details['price']:,.2f}",
                "original_price": f"₹{details['original_price']:,.2f}",
                "discount": f"{details['discount_percent']}% off",
                "rating": f"{details['rating']}/5.0 ({details['review_count']} reviews)",
                "stock_status": stock_status,
                "features": details["features"],
                "specifications": details["specifications"],
                "tags": details["tags"],
            }
            return json.dumps(formatted, indent=2)
    except Exception as e:
        return f"Database error fetching product details: {str(e)}"


@tool
def check_inventory(product_id: int, quantity: int = 1) -> str:
    """Check stock availability for a product ID and quantity."""
    try:
        with get_db_session() as db:
            service = InventoryService(db)
            res = service.check_availability(product_id=product_id, requested_quantity=quantity)
            return json.dumps({
                "product_id": res.product_id,
                "product_name": res.product_name,
                "is_available": res.is_available,
                "status": res.status,
                "message": res.message,
            }, indent=2)
    except Exception as e:
        return f"Database error checking inventory: {str(e)}"


@tool
def add_to_cart(product_id: int, quantity: int = 1) -> str:
    """Add a product to the cart after validating stock availability."""
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
    """Remove a product from the shopping cart."""
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
    """Update item quantity in cart. Setting quantity to 0 removes the item."""
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
    """Retrieve current shopping cart contents, line items, and total price."""
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
    """Completely empty the shopping cart."""
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


SHOPPING_TOOLS = [
    search_products,
    get_product_details,
    check_inventory,
    add_to_cart,
    remove_from_cart,
    update_cart_item,
    get_cart,
    clear_cart,
]

ALL_SHOPPING_TOOLS = SHOPPING_TOOLS

__all__ = [
    "search_products",
    "get_product_details",
    "check_inventory",
    "add_to_cart",
    "remove_from_cart",
    "update_cart_item",
    "clear_cart",
    "get_cart",
    "SHOPPING_TOOLS",
    "ALL_SHOPPING_TOOLS",
]
