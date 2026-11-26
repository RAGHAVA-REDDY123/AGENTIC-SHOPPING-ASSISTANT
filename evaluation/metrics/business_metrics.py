from typing import Dict, Any, List
from backend.security.guardrails import HumanInTheLoopMiddleware


class BusinessMetrics:
    """Verifies deterministic transactional math and database state consistency."""

    @staticmethod
    def verify_cart_subtotal(items: List[Dict[str, float]], expected_subtotal: float) -> bool:
        calculated = sum(i["price"] * i["quantity"] for i in items)
        return float(calculated) == float(expected_subtotal)

    @staticmethod
    def verify_hitl_checkout_gate(confirmed: bool) -> bool:
        allowed, challenge = HumanInTheLoopMiddleware.intercept_destructive_action(
            "checkout_cart", {}, confirmed=confirmed
        )
        if not confirmed:
            return (allowed is False) and (challenge is not None)
        return (allowed is True) and (challenge is None)

    @staticmethod
    def verify_stock_decrement(initial_stock: int, purchased_qty: int, expected_remaining: int) -> bool:
        return (initial_stock - purchased_qty) == expected_remaining
