import math
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from backend.models.product import Product
from backend.repositories.product_repository import ProductRepository
from backend.repositories.review_repository import ReviewRepository


class EmbeddingService:

    model = SentenceTransformer("all-MiniLM-L6-v2")

    @classmethod
    def embed_text(cls, text: str) -> list[float]:
        if not text or not text.strip():
            return [0.0] * 384
        return cls.model.encode(text.strip()).tolist()

    @staticmethod
    def build_product_embedding_text(product: Dict[str, Any]) -> str:
        name = product.get("name", "")
        brand = product.get("brand", "")
        category = product.get("category_slug", "")
        description = product.get("description", "")
        tags = ", ".join(product.get("tags", [])) if isinstance(product.get("tags"), list) else ""
        features = product.get("features", {})
        feat_str = "; ".join(f"{k}: {v}" for k, v in features.items()) if isinstance(features, dict) else ""
        return " | ".join(p for p in [name, brand, category, tags, description, feat_str] if p)


class ProductRankingService:

    @classmethod
    def rank_products(
        cls,
        products: Union[List[Product], List[Tuple[Product, float]]],
        query: Optional[str] = None,
        target_budget: Optional[Decimal] = None,
    ) -> List[Tuple[Product, float, str]]:
        if not products:
            return []

        norm_candidates = [item if isinstance(item, tuple) else (item, 0.0) for item in products]
        max_rrf = max((score for _, score in norm_candidates), default=0.0)
        scored_items: List[Tuple[Product, float, str]] = []

        for p, rrf_score in norm_candidates:
            score = 0.0
            criteria: List[str] = []

            # 1. Semantic / Hybrid Relevance (0-40 pts)
            if max_rrf > 0.0 and rrf_score > 0.0:
                rel_score = (rrf_score / max_rrf) * 40.0
                score += rel_score
                criteria.append(f"Relevance (+{rel_score:.1f}pts)")

            # 2. Rating Quality (0-30 pts)
            rating_score = (float(p.rating) / 5.0) * 30.0
            score += rating_score
            criteria.append(f"Rating {float(p.rating):.1f}/5.0 (+{rating_score:.1f}pts)")

            # 3. Review Volume Credibility (0-15 pts)
            if p.review_count > 0:
                review_score = min(math.log10(p.review_count + 1) / 3.0, 1.0) * 15.0
                score += review_score
                criteria.append(f"{p.review_count:,} reviews (+{review_score:.1f}pts)")

            # 4. Budget fit & Deal (0-15 pts)
            price_val = float(p.price)
            if target_budget and target_budget > 0:
                budget_val = float(target_budget)
                if price_val <= budget_val:
                    score += 10.0
                    criteria.append(f"Within budget (+10.0pts)")
                else:
                    penalty = min(((price_val - budget_val) / budget_val) * 15.0, 15.0)
                    score -= penalty
                    criteria.append(f"Over budget (-{penalty:.1f}pts)")

            if p.discount_percent > 0:
                disc_score = (p.discount_percent / 100.0) * 5.0
                score += disc_score
                criteria.append(f"{p.discount_percent}% off (+{disc_score:.1f}pts)")

            scored_items.append((p, round(score, 2), "; ".join(criteria)))

        scored_items.sort(key=lambda item: item[1], reverse=True)
        return scored_items


class ProductService:

    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)

    def search_products(
        self,
        query: Optional[str] = None,
        category_slug: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        min_rating: Optional[Decimal] = None,
        target_budget: Optional[Decimal] = None,
        apply_ranking: bool = True,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
    
        # Compute vector embedding for semantic search
        query_vector = None
        if query and query.strip():
            try:
                query_vector = EmbeddingService.embed_text(query.strip())
            except Exception:
                query_vector = None

        try:
            candidates = self.product_repo.search(
                query=query,
                query_vector=query_vector,
                category_slug=category_slug,
                brand=brand,
                min_price=min_price,
                max_price=max_price,
                min_rating=min_rating,
                limit=limit * 2 if apply_ranking else limit,
                offset=offset,
            )
        except Exception:
            # Graceful recovery on database timeout or connection error
            return []

        if not candidates:
            return []

        if apply_ranking:
            effective_budget = target_budget if target_budget is not None else max_price
            ranked = ProductRankingService.rank_products(candidates, query=query, target_budget=effective_budget)[:limit]
            results = []
            for rank_idx, (p, score, explanation) in enumerate(ranked, start=1):
                stock = (p.inventory.stock_quantity - p.inventory.reserved_quantity) if p.inventory else 0
                results.append({
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "brand": p.brand,
                    "category_slug": p.category_slug,
                    "price": float(p.price),
                    "original_price": float(p.original_price),
                    "discount_percent": p.discount_percent,
                    "rating": float(p.rating),
                    "review_count": p.review_count,
                    "in_stock": stock > 0,
                    "stock_quantity": stock,
                    "rank": rank_idx,
                    "ranking_score": score,
                    "ranking_criteria": explanation,
                    "features": p.features,
                    "image_url": p.image_url,
                })
            return results
        else:
            results = []
            for p, _score in candidates[:limit]:
                stock = (p.inventory.stock_quantity - p.inventory.reserved_quantity) if p.inventory else 0
                results.append({
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "brand": p.brand,
                    "category_slug": p.category_slug,
                    "price": float(p.price),
                    "original_price": float(p.original_price),
                    "discount_percent": p.discount_percent,
                    "rating": float(p.rating),
                    "review_count": p.review_count,
                    "in_stock": stock > 0,
                    "stock_quantity": stock,
                    "features": p.features,
                    "image_url": p.image_url,
                })
            return results

    def get_product_details(
        self, identifier: Union[int, str], review_topic: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        product = self.product_repo.get_by_id(int(identifier)) if str(identifier).isdigit() else self.product_repo.get_by_slug(str(identifier))
        if not product:
            return None

        stock = (product.inventory.stock_quantity - product.inventory.reserved_quantity) if product.inventory else 0

        reviews_data = []
        if review_topic:
            query_vector = None
            clean_focus = review_topic.strip().lower()
            if clean_focus not in ("best", "positive", "top", "worst", "critical", "negative", "complaints", "summary"):
                try:
                    query_vector = EmbeddingService.embed_text(review_topic.strip())
                except Exception:
                    query_vector = None

            review_repo = ReviewRepository(self.db)
            matched = review_repo.get_reviews_for_product(
                product_id=product.id,
                focus=review_topic,
                query_vector=query_vector,
                limit=3,
            )
            reviews_data = [
                {
                    "rating": f"{r.rating}★",
                    "title": r.title,
                    "comment": r.comment,
                    "author": r.author_name,
                }
                for r in matched
            ]

        data = {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "description": product.description,
            "brand": product.brand,
            "category_slug": product.category_slug,
            "price": float(product.price),
            "original_price": float(product.original_price),
            "discount_percent": product.discount_percent,
            "rating": float(product.rating),
            "review_count": product.review_count,
            "features": product.features,
            "specifications": product.specifications,
            "tags": product.tags,
            "in_stock": stock > 0,
            "stock_quantity": stock,
            "image_url": product.image_url,
        }
        if review_topic:
            data["review_topic"] = review_topic
            data["customer_reviews"] = reviews_data

        return data

