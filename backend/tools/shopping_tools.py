import json
from decimal import Decimal
from typing import Optional
from langchain_core.tools import tool

from backend.database.connection import get_db_session
from backend.security.guardrails import HumanInTheLoopMiddleware
from backend.services.cart_service import CartService
from backend.services.inventory_service import InventoryService
from backend.services.order_service import OrderService
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
        query = HumanInTheLoopMiddleware.sanitize_search_query(query)
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
                    stock_status = "low_stock"
                else:
                    stock_status = "in_stock"

                # Extract top 2 feature highlights to keep payload compact
                feats = p.get("features", {})
                highlight = "; ".join(f"{k}: {v}" for k, v in list(feats.items())[:2]) if isinstance(feats, dict) else ""

                formatted.append({
                    "id": p["id"],
                    "name": p["name"],
                    "brand": p["brand"],
                    "price": f"₹{p['price']:,.2f}",
                    "rating": f"{p['rating']}/5.0",
                    "stock_status": stock_status,
                    "highlights": highlight,
                })

            return json.dumps(formatted, separators=(",", ":"))
    except Exception as e:
        return f"Database error during product search: {str(e)}"


@tool
def get_product_details(identifier: str, review_topic: Optional[str] = None) -> str:
    """
    Retrieve product specifications, features, or verified customer reviews.
    
    Args:
        identifier: Product ID or slug (e.g. '1', 'oneplus-12-5g', 'asus-rog-strix-g15-gaming').
        review_topic: Optional review aspect to inspect verified buyer opinions:
                      - 'summary' (overall buyer consensus, pros & cons)
                      - 'best' (top 5-star positive reviews)
                      - 'worst' (critical negative reviews & complaints)
                      - Specific topic (e.g. 'camera', 'battery life', 'heating', 'display', 'fan noise').
    """
    try:
        with get_db_session() as db:
            service = ProductService(db)
            details = service.get_product_details(identifier, review_topic=review_topic)
            if not details:
                return f"Product '{identifier}' was not found in the catalog."

            stock_qty = details.get("stock_quantity", 0)
            if not details.get("in_stock", False) or stock_qty <= 0:
                stock_status = "out_of_stock"
            elif stock_qty <= 3:
                stock_status = "low_stock"
            else:
                stock_status = "in_stock"

            formatted = {
                "id": details["id"],
                "name": details["name"],
                "brand": details["brand"],
                "category": details["category_slug"],
                "price": f"₹{details['price']:,.2f}",
                "rating": f"{details['rating']}/5.0 ({details['review_count']} reviews)",
                "stock_status": stock_status,
                "features": details["features"],
                "specifications": details["specifications"],
            }
            if "customer_reviews" in details:
                formatted["review_topic"] = details.get("review_topic")
                formatted["matched_reviews"] = details["customer_reviews"]

            return json.dumps(formatted, separators=(",", ":"))
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
    """
    Add a product to the cart. Returns the updated cart summary immediately.
    Do NOT call get_cart after calling this tool.
    """
    try:
        quantity = HumanInTheLoopMiddleware.validate_cart_quantity(quantity)
        with get_db_session() as db:
            service = CartService(db)
            res = service.add_to_cart(product_id=product_id, quantity=quantity)
            if not res.success or not res.cart:
                return json.dumps({"success": False, "message": res.message})

            compact_items = [
                {"name": it.product_name, "qty": it.quantity, "subtotal": f"₹{float(it.subtotal):,.2f}"}
                for it in res.cart.items
            ]
            return json.dumps({
                "success": True,
                "message": res.message,
                "cart": {
                    "total_items": res.cart.total_items,
                    "total_price": f"₹{float(res.cart.total_price):,.2f}",
                    "items": compact_items,
                },
            }, separators=(",", ":"))
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
        quantity = HumanInTheLoopMiddleware.validate_cart_quantity(quantity, min_val=0, max_val=10)
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
            compact = {
                "total_items": cart.total_items,
                "total_price": f"₹{float(cart.total_price):,.2f}",
                "items": [
                    {"name": it.product_name, "quantity": it.quantity, "subtotal": f"₹{float(it.subtotal):,.2f}"}
                    for it in cart.items
                ],
            }
            return json.dumps(compact, separators=(",", ":"))
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


@tool
def get_saved_addresses() -> str:
    """Retrieve the customer's saved delivery addresses."""
    try:
        with get_db_session() as db:
            service = OrderService(db)
            addresses = service.get_saved_addresses()
            if not addresses:
                return "No saved addresses found. Please provide your delivery address."
            return json.dumps(addresses, indent=2)
    except Exception as e:
        return f"Database error fetching addresses: {str(e)}"


@tool
def add_saved_address(
    recipient_name: str,
    phone: str,
    address_line: str,
    city: str,
    state: str,
    pincode: str,
    title: str = "Home",
    is_default: bool = False,
) -> str:
    """Save a new delivery address for the customer."""
    try:
        # Layer 3 Detokenization: resolve PII tokens back to real values for DB
        recipient_name = HumanInTheLoopMiddleware.detokenize_tool_argument(recipient_name)
        phone = HumanInTheLoopMiddleware.detokenize_tool_argument(phone)
        address_line = HumanInTheLoopMiddleware.detokenize_tool_argument(address_line)

        with get_db_session() as db:
            service = OrderService(db)
            res = service.add_saved_address(
                recipient_name=recipient_name,
                phone=phone,
                address_line=address_line,
                city=city,
                state=state,
                pincode=pincode,
                title=title,
                is_default=is_default,
            )
            return json.dumps(res, indent=2)
    except Exception as e:
        return f"Database error adding address: {str(e)}"


@tool
def checkout_cart(
    shipping_address: Optional[str] = None,
    contact_phone: Optional[str] = None,
    recipient_name: Optional[str] = None,
    address_id: Optional[int] = None,
) -> str:
    """
    Finalize the shopping cart and place an order using Cash on Delivery (COD).
    Call this ONLY after the user has reviewed the order summary and explicitly confirmed placing the order.
    
    Args:
        shipping_address: Full delivery address text (if not using address_id).
        contact_phone: 10-digit contact mobile number (if not using address_id).
        recipient_name: Optional recipient name.
        address_id: Optional integer ID of a chosen saved address.
    """
    try:
        # Layer 3 Detokenization: resolve PII tokens back to real values for DB
        shipping_address = HumanInTheLoopMiddleware.detokenize_tool_argument(shipping_address)
        contact_phone = HumanInTheLoopMiddleware.detokenize_tool_argument(contact_phone)
        recipient_name = HumanInTheLoopMiddleware.detokenize_tool_argument(recipient_name)

        with get_db_session() as db:
            service = OrderService(db)
            res = service.checkout_cart(
                shipping_address=shipping_address,
                contact_phone=contact_phone,
                recipient_name=recipient_name,
                address_id=address_id,
            )
            return json.dumps(res, indent=2)
    except Exception as e:
        return f"Database error placing order: {str(e)}"


@tool
def track_order(order_number: str) -> str:
    """Track the status and details of an existing order using its order number (e.g. 'ORD-20261124-7A9B')."""
    try:
        with get_db_session() as db:
            service = OrderService(db)
            res = service.track_order(order_number=order_number)
            return json.dumps(res, indent=2)
    except Exception as e:
        return f"Database error tracking order: {str(e)}"


@tool
def get_order_history() -> str:
    """Retrieve the customer's previous order history and past purchases."""
    try:
        with get_db_session() as db:
            service = OrderService(db)
            orders = service.get_order_history()
            if not orders:
                return "You have not placed any orders yet."
            return json.dumps(orders, indent=2)
    except Exception as e:
        return f"Database error fetching order history: {str(e)}"


@tool
def cancel_order(order_number: str, reason: str = "") -> str:
    """Cancel an active order by order number and restore product stock."""
    try:
        with get_db_session() as db:
            service = OrderService(db)
            res = service.cancel_order(order_number=order_number, reason=reason)
            return json.dumps(res, indent=2)
    except Exception as e:
        return f"Database error cancelling order: {str(e)}"


SHOPPING_TOOLS = [
    search_products,
    get_product_details,
    check_inventory,
    add_to_cart,
    remove_from_cart,
    update_cart_item,
    get_cart,
    clear_cart,
    get_saved_addresses,
    add_saved_address,
    checkout_cart,
    track_order,
    get_order_history,
    cancel_order,
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
    "get_saved_addresses",
    "add_saved_address",
    "checkout_cart",
    "track_order",
    "get_order_history",
    "cancel_order",
    "SHOPPING_TOOLS",
    "ALL_SHOPPING_TOOLS",
]
