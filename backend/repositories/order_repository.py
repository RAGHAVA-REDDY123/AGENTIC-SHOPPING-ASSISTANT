from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.models.order import CustomerAddress, Order, OrderItem


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_addresses(self, customer_id: str) -> List[CustomerAddress]:
        stmt = (
            select(CustomerAddress)
            .where(CustomerAddress.customer_id == customer_id)
            .order_by(CustomerAddress.is_default.desc(), CustomerAddress.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_default_address(self, customer_id: str) -> Optional[CustomerAddress]:
        stmt = (
            select(CustomerAddress)
            .where(CustomerAddress.customer_id == customer_id, CustomerAddress.is_default.is_(True))
            .limit(1)
        )
        addr = self.db.scalars(stmt).first()
        if not addr:
            addr = self.db.scalars(
                select(CustomerAddress)
                .where(CustomerAddress.customer_id == customer_id)
                .order_by(CustomerAddress.created_at.desc())
                .limit(1)
            ).first()
        return addr

    def add_address(
        self,
        customer_id: str,
        title: str,
        recipient_name: str,
        phone: str,
        address_line: str,
        city: str,
        state: str,
        pincode: str,
        is_default: bool = False,
    ) -> CustomerAddress:
        if is_default:
            existing = self.get_addresses(customer_id)
            for a in existing:
                a.is_default = False

        address = CustomerAddress(
            customer_id=customer_id,
            title=title,
            recipient_name=recipient_name,
            phone=phone,
            address_line=address_line,
            city=city,
            state=state,
            pincode=pincode,
            is_default=is_default,
        )
        self.db.add(address)
        self.db.flush()
        return address

    def create_order(
        self,
        customer_id: str,
        order_number: str,
        total_amount,
        shipping_address: str,
        contact_phone: str,
        items_data: list,
        payment_method: str = "COD",
        payment_status: str = "PENDING",
    ) -> Order:
        order = Order(
            customer_id=customer_id,
            order_number=order_number,
            status="CONFIRMED",
            total_amount=total_amount,
            payment_method=payment_method,
            payment_status=payment_status,
            shipping_address=shipping_address,
            contact_phone=contact_phone,
        )
        self.db.add(order)
        self.db.flush()

        for item in items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product_id"],
                product_name=item["product_name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                subtotal=item["subtotal"],
            )
            self.db.add(order_item)

        self.db.flush()
        return order

    def get_by_order_number(self, order_number: str, customer_id: Optional[str] = None) -> Optional[Order]:
        stmt = (
            select(Order)
            .options(joinedload(Order.items))
            .where(Order.order_number == order_number.strip().upper())
        )
        if customer_id:
            stmt = stmt.where(Order.customer_id == customer_id)
        return self.db.scalars(stmt).unique().first()

    def get_customer_orders(self, customer_id: str, limit: int = 10) -> List[Order]:
        stmt = (
            select(Order)
            .options(joinedload(Order.items))
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())

    def update_status(self, order: Order, new_status: str) -> Order:
        order.status = new_status
        self.db.flush()
        return order

