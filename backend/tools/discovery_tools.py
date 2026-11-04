import json
from decimal import Decimal
from typing import Optional
from langchain_core.tools import tool

from backend.database.connection import get_db_session
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
    Search product catalog using hybrid pgvector semantic similarity, SQL filtering, and commercial reranking.

    Args:
        query: Natural language query or keywords
        category_slug: Category slug (e.g. 'laptops', 'mobiles', 'accessories', 'headphones')
        brand: Brand name filter (e.g. 'Apple', 'ASUS', 'Samsung', 'Sony', 'Dell')
        min_price: Minimum price filter
        max_price: Maximum price filter
        min_rating: Minimum customer rating filter (e.g. 4.0)
        target_budget: Target spending budget to rank value-for-money products
        limit: Maximum number of products to return (default 5, max 20)
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
                return "No products matched your search criteria. Please adjust keywords or budget filters."

            formatted = []
            for p in results:
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
                    "in_stock": p["in_stock"],
                    "ranking_score": p["ranking_score"],
                    "ranking_criteria": p["ranking_criteria"],
                    "key_features": p["features"],
                })

            return json.dumps(formatted, indent=2)
    except Exception as e:
        return f"Database error during product search: {str(e)}"


@tool
def get_product_details(identifier: str) -> str:
    """
    Retrieve comprehensive details, specifications, features, and real-time inventory for a single product.

    Args:
        identifier: The product ID (e.g. '1') or unique product slug (e.g. 'asus-rog-strix-g15-gaming')
    """
    try:
        with get_db_session() as db:
            service = ProductService(db)
            details = service.get_product_details(identifier)
            if not details:
                return f"Product '{identifier}' was not found in the catalog."

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
                "rating": f"{details['rating']}/5.0 based on {details['review_count']} verified reviews",
                "in_stock": details["in_stock"],
                "available_stock": details["stock_quantity"],
                "features": details["features"],
                "specifications": details["specifications"],
                "tags": details["tags"],
            }
            return json.dumps(formatted, indent=2)
    except Exception as e:
        return f"Database error fetching product details: {str(e)}"


@tool
def check_inventory(product_id: int, quantity: int = 1) -> str:
    """
    Check physical stock availability for a specific product ID and requested quantity.

    Args:
        product_id: The integer ID of the product
        quantity: The quantity to check (defaults to 1)
    """
    try:
        with get_db_session() as db:
            service = InventoryService(db)
            res = service.check_availability(product_id=product_id, requested_quantity=quantity)
            return json.dumps({
                "product_id": res.product_id,
                "product_name": res.product_name,
                "is_available": res.is_available,
                "available_stock": res.stock_quantity,
                "requested_quantity": res.requested_quantity,
                "status": res.status,
                "message": res.message,
            }, indent=2)
    except Exception as e:
        return f"Database error checking inventory: {str(e)}"


DISCOVERY_TOOLS = [
    search_products,
    get_product_details,
    check_inventory,
]

