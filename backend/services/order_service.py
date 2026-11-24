import os
import secrets
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.models.order import Order
from backend.repositories.cart_repository import CartRepository
from backend.repositories.inventory_repository import InventoryRepository
from backend.repositories.order_repository import OrderRepository
from backend.repositories.product_repository import ProductRepository
from backend.services.inventory_service import InventoryService


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)
        self.product_repo = ProductRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.inventory_service = InventoryService(db)

    def get_saved_addresses(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        cid = customer_id or os.getenv("DEV_CUSTOMER_ID", "dev_customer_001")
        addresses = self.order_repo.get_addresses(cid)
        return [
            {
                "id": a.id,
                "title": a.title,
                "recipient_name": a.recipient_name,
                "phone": a.phone,
                "address": f"{a.address_line}, {a.city}, {a.state} - {a.pincode}",
                "is_default": a.is_default,
            }
            for a in addresses
        ]

    def add_saved_address(
        self,
        recipient_name: str,
        phone: str,
        address_line: str,
        city: str,
        state: str,
        pincode: str,
        title: str = "Home",
        is_default: bool = False,
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        cid = customer_id or os.getenv("DEV_CUSTOMER_ID", "dev_customer_001")
        address = self.order_repo.add_address(
            customer_id=cid,
            title=title,
            recipient_name=recipient_name,
            phone=phone,
            address_line=address_line,
            city=city,
            state=state,
            pincode=pincode,
            is_default=is_default,
        )
        self.db.commit()
        return {
            "success": True,
            "address_id": address.id,
            "title": address.title,
            "formatted_address": address.to_formatted_string(),
        }

    def checkout_cart(
        self,
        shipping_address: Optional[str] = None,
        contact_phone: Optional[str] = None,
        recipient_name: Optional[str] = None,
        address_id: Optional[int] = None,
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        cid = customer_id or os.getenv("DEV_CUSTOMER_ID", "dev_customer_001")
        cart = self.cart_repo.get_cart(cid)

        if not cart or not cart.items:
            return {
                "success": False,
                "message": "Your shopping cart is empty. Add products to your cart before checking out.",
            }

        # Resolve address
        final_address = ""
        final_phone = ""
        final_name = recipient_name or "Valued Customer"

        if address_id:
            addresses = self.order_repo.get_addresses(cid)
            matched = next((a for a in addresses if a.id == address_id), None)
            if matched:
                final_address = matched.to_formatted_string()
                final_phone = matched.phone
                final_name = matched.recipient_name

        if not final_address and shipping_address and contact_phone:
            final_address = f"{final_name}, {shipping_address.strip()} (Phone: {contact_phone.strip()})"
            final_phone = contact_phone.strip()

        if not final_address:
            default_addr = self.order_repo.get_default_address(cid)
            if default_addr:
                final_address = default_addr.to_formatted_string()
                final_phone = default_addr.phone
                final_name = default_addr.recipient_name

        if not final_address or not final_phone:
            saved = self.get_saved_addresses(cid)
            return {
                "success": False,
                "needs_address": True,
                "message": "Delivery address and contact phone are required to place the order.",
                "saved_addresses": saved,
            }

        # Validate stock availability for all items
        items_data = []
        total_amount = Decimal("0.00")

        for item in cart.items:
            check = self.inventory_service.check_availability(item.product_id, item.quantity)
            if not check.is_available:
                return {
                    "success": False,
                    "message": f"Cannot complete order: {check.message}",
                }

            subtotal = item.product.price * Decimal(item.quantity)
            total_amount += subtotal
            items_data.append({
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.product.price,
                "subtotal": subtotal,
            })

        # Generate unique order number
        date_prefix = datetime.now().strftime("%Y%m%d")
        random_suffix = secrets.token_hex(3).upper()
        order_number = f"ORD-{date_prefix}-{random_suffix}"

        # Create Order atomically
        order = self.order_repo.create_order(
            customer_id=cid,
            order_number=order_number,
            total_amount=total_amount,
            shipping_address=final_address,
            contact_phone=final_phone,
            items_data=items_data,
            payment_method="COD",
            payment_status="PENDING",
        )

        # Deduct physical stock
        for item in items_data:
            self.inventory_repo.update_stock(item["product_id"], -item["quantity"])

        # Clear cart
        for item in list(cart.items):
            self.cart_repo.remove_item(cart.id, item.product_id)

        self.db.commit()

        return {
            "success": True,
            "order_number": order.order_number,
            "status": order.status,
            "payment_method": "Cash on Delivery (COD)",
            "total_amount": f"₹{float(order.total_amount):,.2f}",
            "shipping_address": order.shipping_address,
            "contact_phone": order.contact_phone,
            "items_count": len(items_data),
            "items": [
                {
                    "name": i["product_name"],
                    "quantity": i["quantity"],
                    "price": f"₹{float(i['unit_price']):,.2f}",
                    "subtotal": f"₹{float(i['subtotal']):,.2f}",
                }
                for i in items_data
            ],
            "message": f"Order {order.order_number} confirmed successfully! Pay on delivery.",
        }

    def _resolve_live_status(self, order: Order) -> Dict[str, str]:
        """Simulate realistic delivery progression based on elapsed time since order creation."""
        if order.status == "CANCELLED":
            return {
                "status": "CANCELLED",
                "description": "Order was cancelled by the customer.",
                "delivery_estimate": "N/A",
            }

        now = datetime.now(order.created_at.tzinfo) if order.created_at.tzinfo else datetime.now()
        elapsed_seconds = (now - order.created_at).total_seconds()

        if elapsed_seconds < 120:
            status = "CONFIRMED"
            desc = "Order confirmed. Warehouse is picking and packaging your items."
            estimate = "Expected in 2-3 business days"
        elif elapsed_seconds < 600:
            status = "PROCESSING"
            desc = "Package is packed and labeled, ready for courier dispatch."
            estimate = "Expected in 2 business days"
        elif elapsed_seconds < 1800:
            status = "SHIPPED"
            desc = "Dispatched and in transit with express courier."
            estimate = "Expected tomorrow by 8:00 PM"
        elif elapsed_seconds < 3600:
            status = "OUT_FOR_DELIVERY"
            desc = "Package is out for delivery with the local delivery agent."
            estimate = "Expected today by 6:00 PM"
        else:
            status = "DELIVERED"
            desc = "Delivered to recipient. Package received."
            estimate = "Delivered"

        # Persist updated status to database
        if order.status != status:
            order.status = status
            if status == "DELIVERED" and order.payment_method == "COD":
                order.payment_status = "COMPLETED"
            self.db.commit()

        return {
            "status": status,
            "description": desc,
            "delivery_estimate": estimate,
        }

    def track_order(self, order_number: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        cid = customer_id or os.getenv("DEV_CUSTOMER_ID", "dev_customer_001")
        order = self.order_repo.get_by_order_number(order_number, cid)
        if not order:
            return {
                "success": False,
                "message": f"Order '{order_number}' not found for your account.",
            }

        tracking_info = self._resolve_live_status(order)

        return {
            "success": True,
            "order_number": order.order_number,
            "status": tracking_info["status"],
            "status_description": tracking_info["description"],
            "delivery_estimate": tracking_info["delivery_estimate"],
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "total_amount": f"₹{float(order.total_amount):,.2f}",
            "placed_on": order.created_at.strftime("%d %b %Y, %I:%M %p"),
            "shipping_address": order.shipping_address,
            "items": [
                {
                    "product": item.product_name,
                    "quantity": item.quantity,
                    "price": f"₹{float(item.unit_price):,.2f}",
                    "subtotal": f"₹{float(item.subtotal):,.2f}",
                }
                for item in order.items
            ],
        }

    def get_order_history(self, customer_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        cid = customer_id or os.getenv("DEV_CUSTOMER_ID", "dev_customer_001")
        orders = self.order_repo.get_customer_orders(cid, limit=limit)
        if not orders:
            return []

        history = []
        for o in orders:
            tracking_info = self._resolve_live_status(o)
            history.append({
                "order_number": o.order_number,
                "status": tracking_info["status"],
                "status_description": tracking_info["description"],
                "total_amount": f"₹{float(o.total_amount):,.2f}",
                "payment_method": o.payment_method,
                "placed_on": o.created_at.strftime("%d %b %Y"),
                "items_summary": ", ".join(f"{it.product_name} x{it.quantity}" for it in o.items),
            })
        return history
        

    def cancel_order(self, order_number: str, reason: str = "", customer_id: Optional[str] = None) -> Dict[str, Any]:
        cid = customer_id or os.getenv("DEV_CUSTOMER_ID", "dev_customer_001")
        order = self.order_repo.get_by_order_number(order_number, cid)

        if not order:
            return {
                "success": False,
                "message": f"Order '{order_number}' was not found.",
            }

        if order.status == "CANCELLED":
            return {
                "success": False,
                "message": f"Order '{order_number}' is already cancelled.",
            }

        if order.status in ("SHIPPED", "DELIVERED"):
            return {
                "success": False,
                "message": f"Order '{order_number}' cannot be cancelled as it is already {order.status.lower()}.",
            }

        # Restore inventory stock
        for item in order.items:
            self.inventory_repo.update_stock(item.product_id, item.quantity)

        self.order_repo.update_status(order, "CANCELLED")
        self.db.commit()

        return {
            "success": True,
            "order_number": order.order_number,
            "status": "CANCELLED",
            "message": f"Order '{order.order_number}' has been cancelled successfully. Stock has been restored.",
        }

