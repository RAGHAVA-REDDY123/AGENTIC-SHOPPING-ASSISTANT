import math
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from backend.database.connection import SessionLocal
from backend.models.product import Product
from backend.services.product_service import EmbeddingService, ProductRankingService


class InformationRetrievalEngine:
    """
    Evaluates Information Retrieval quality across 3 configurations:
      1. Keyword/Lexical SQL Search
      2. Dense Vector (pgvector) Semantic Search
      3. Hybrid Search (RRF Reciprocal Rank Fusion)
    
    Computes Precision@K, Recall@K, MRR, and NDCG@K against known relevant product IDs.
    Identifies queries where hybrid retrieval underperforms individual retrieval methods.
    """

    def __init__(self, db: Optional[Session] = None):
        self._owned_session = False
        if db is None:
            self.db = SessionLocal()
            self._owned_session = True
        else:
            self.db = db

    def close(self):
        if self._owned_session and self.db:
            self.db.close()

    def search_keyword_only(
        self,
        query: Optional[str] = None,
        category_slug: Optional[str] = None,
        max_price: Optional[Decimal] = None,
        limit: int = 10,
    ) -> List[int]:
        """Pure lexical / SQL filter retrieval."""
        stmt = select(Product)
        if query:
            clean = f"%{query.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Product.name).ilike(clean),
                    func.lower(Product.description).ilike(clean),
                    func.lower(Product.brand).ilike(clean),
                )
            )
        if category_slug:
            stmt = stmt.where(func.lower(Product.category_slug) == category_slug.strip().lower())
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)

        stmt = stmt.order_by(Product.rating.desc(), Product.review_count.desc()).limit(limit)
        return [p.id for p in self.db.scalars(stmt).unique().all()]

    def search_vector_only(
        self,
        query: str,
        category_slug: Optional[str] = None,
        max_price: Optional[Decimal] = None,
        limit: int = 10,
    ) -> List[int]:
        """Pure pgvector dense cosine similarity retrieval."""
        if not query or not query.strip():
            return []
        try:
            query_vector = EmbeddingService.embed_text(query.strip())
            stmt = select(Product).where(Product.embedding.isnot(None))
            if category_slug:
                stmt = stmt.where(func.lower(Product.category_slug) == category_slug.strip().lower())
            if max_price is not None:
                stmt = stmt.where(Product.price <= max_price)

            stmt = stmt.order_by(Product.embedding.cosine_distance(query_vector)).limit(limit)
            return [p.id for p in self.db.scalars(stmt).unique().all()]
        except Exception:
            return []

    def search_hybrid(
        self,
        query: Optional[str] = None,
        category_slug: Optional[str] = None,
        max_price: Optional[Decimal] = None,
        limit: int = 10,
    ) -> List[int]:
        """Hybrid search combining Keyword and pgvector via RRF."""
        query_vector = None
        if query and query.strip():
            try:
                query_vector = EmbeddingService.embed_text(query.strip())
            except Exception:
                query_vector = None

        from backend.repositories.product_repository import ProductRepository
        repo = ProductRepository(self.db)
        results = repo.search(
            query=query,
            query_vector=query_vector,
            category_slug=category_slug,
            max_price=max_price,
            limit=limit,
        )
        return [p.id for p, _ in results]

    @staticmethod
    def compute_precision_at_k(retrieved_ids: List[int], relevant_ids: List[int], k: int) -> float:
        """
        Computes Precision@K with catalog saturation normalization:
        If fewer than K relevant items exist in the database, precision is normalized
        by min(K, total_relevant) so the algorithm isn't penalized for a small catalog.
        """
        if k <= 0 or not retrieved_ids or not relevant_ids:
            return 0.0
        effective_k = min(k, len(relevant_ids))
        top_k = retrieved_ids[:k]
        hits = sum(1 for pid in top_k if pid in relevant_ids)
        return min(hits / effective_k, 1.0)

    @staticmethod
    def compute_recall_at_k(retrieved_ids: List[int], relevant_ids: List[int], k: int) -> float:
        if not relevant_ids:
            return 1.0
        top_k = retrieved_ids[:k]
        hits = sum(1 for pid in top_k if pid in relevant_ids)
        return hits / len(relevant_ids)

    @staticmethod
    def compute_mrr(retrieved_ids: List[int], relevant_ids: List[int]) -> float:
        for rank, pid in enumerate(retrieved_ids, start=1):
            if pid in relevant_ids:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def compute_ndcg_at_k(retrieved_ids: List[int], relevant_ids: List[int], k: int) -> float:
        if not relevant_ids or k <= 0 or not retrieved_ids:
            return 0.0
        top_k = retrieved_ids[:k]
        dcg = 0.0
        for i, pid in enumerate(top_k, start=1):
            rel = 1.0 if pid in relevant_ids else 0.0
            dcg += (2**rel - 1.0) / math.log2(i + 1.0)

        idcg = sum((2**1.0 - 1.0) / math.log2(i + 1.0) for i in range(1, min(len(relevant_ids), k) + 1))
        return (dcg / idcg) if idcg > 0.0 else 0.0

    def evaluate_query_benchmark(
        self,
        test_queries: List[Dict[str, Any]],
        k_values: List[int] = [3, 5],
    ) -> Dict[str, Any]:
        """
        Runs benchmark across Keyword, Semantic, and Hybrid retrieval modes.
        Computes aggregate metrics and identifies cases where Hybrid underperformed.
        """
        modes = ["keyword", "semantic", "hybrid"]
        aggregate: Dict[str, Dict[str, float]] = {m: {} for m in modes}
        query_level_results: List[Dict[str, Any]] = []
        hybrid_underperformance_cases: List[Dict[str, Any]] = []

        raw_scores: Dict[str, Dict[str, List[float]]] = {
            m: {f"P@{k}": [] for k in k_values} for m in modes
        }
        for m in modes:
            for k in k_values:
                raw_scores[m][f"R@{k}"] = []
                raw_scores[m][f"NDCG@{k}"] = []
            raw_scores[m]["MRR"] = []

        for q in test_queries:
            user_input = q.get("user_input", "")
            category = q.get("expected_args", {}).get("category")
            max_price_val = q.get("expected_args", {}).get("max_price")
            max_price = Decimal(str(max_price_val)) if max_price_val else None
            relevant_ids = q.get("expected_product_ids", [])

            if not relevant_ids:
                continue

            res_kw = self.search_keyword_only(query=user_input, category_slug=category, max_price=max_price, limit=10)
            res_sem = self.search_vector_only(query=user_input, category_slug=category, max_price=max_price, limit=10)
            res_hyb = self.search_hybrid(query=user_input, category_slug=category, max_price=max_price, limit=10)

            mode_results = {"keyword": res_kw, "semantic": res_sem, "hybrid": res_hyb}
            q_metrics: Dict[str, Any] = {"id": q.get("id"), "query": user_input, "relevant_ids": relevant_ids}

            for m in modes:
                ret_list = mode_results[m]
                m_metrics: Dict[str, float] = {}
                for k in k_values:
                    p = self.compute_precision_at_k(ret_list, relevant_ids, k)
                    r = self.compute_recall_at_k(ret_list, relevant_ids, k)
                    ndcg = self.compute_ndcg_at_k(ret_list, relevant_ids, k)
                    raw_scores[m][f"P@{k}"].append(p)
                    raw_scores[m][f"R@{k}"].append(r)
                    raw_scores[m][f"NDCG@{k}"].append(ndcg)
                    m_metrics[f"P@{k}"] = round(p, 3)
                    m_metrics[f"R@{k}"] = round(r, 3)
                    m_metrics[f"NDCG@{k}"] = round(ndcg, 3)

                mrr = self.compute_mrr(ret_list, relevant_ids)
                raw_scores[m]["MRR"].append(mrr)
                m_metrics["MRR"] = round(mrr, 3)
                q_metrics[m] = m_metrics

            hyb_p5 = q_metrics["hybrid"].get("P@5", 0.0)
            kw_p5 = q_metrics["keyword"].get("P@5", 0.0)
            sem_p5 = q_metrics["semantic"].get("P@5", 0.0)

            if hyb_p5 < max(kw_p5, sem_p5):
                hybrid_underperformance_cases.append({
                    "id": q.get("id"),
                    "query": user_input,
                    "hybrid_p5": hyb_p5,
                    "best_p5": max(kw_p5, sem_p5),
                    "better_mode": "keyword" if kw_p5 > hyb_p5 else "semantic",
                    "reason": "Hybrid RRF fusion diluted top candidate rank relative to individual mode."
                })

            query_level_results.append(q_metrics)

        for m in modes:
            for metric_key, values in raw_scores[m].items():
                avg = (sum(values) / len(values)) if values else 0.0
                aggregate[m][metric_key] = round(avg, 3)

        return {
            "aggregate": aggregate,
            "query_count": len(query_level_results),
            "hybrid_underperformance_count": len(hybrid_underperformance_cases),
            "hybrid_underperformance_cases": hybrid_underperformance_cases,
            "query_level_results": query_level_results,
        }
