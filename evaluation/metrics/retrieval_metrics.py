from decimal import Decimal
from typing import Dict, Any
from evaluation.evaluators.retrieval_evaluator import RetrievalEvaluator


class RetrievalMetrics:
    """Computes Precision@K and catalog ranking metrics."""

    @staticmethod
    def compute_precision_at_5(category_slug: str, max_price: float) -> Dict[str, Any]:
        return RetrievalEvaluator.evaluate_precision_at_k(category_slug, Decimal(str(max_price)), k=5)
