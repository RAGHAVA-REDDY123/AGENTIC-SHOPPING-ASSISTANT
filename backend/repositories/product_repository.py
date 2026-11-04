from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from backend.models.product import Product


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, product_id: int) -> Optional[Product]:
        stmt = select(Product).options(joinedload(Product.inventory)).where(Product.id == product_id)
        return self.db.scalars(stmt).first()

    def get_by_slug(self, slug: str) -> Optional[Product]:
        stmt = select(Product).options(joinedload(Product.inventory)).where(Product.slug == slug)
        return self.db.scalars(stmt).first()

    def get_by_ids(self, product_ids: List[int]) -> List[Product]:
        if not product_ids:
            return []
        stmt = select(Product).options(joinedload(Product.inventory)).where(Product.id.in_(product_ids))
        return list(self.db.scalars(stmt).all())

    def find_by_name_or_keyword(self, query: str) -> Optional[Product]:
        clean = query.strip()
        if not clean:
            return None

        stmt = (
            select(Product)
            .options(joinedload(Product.inventory))
            .where(
                or_(
                    func.lower(Product.name).ilike(f"%{clean.lower()}%"),
                    func.lower(Product.slug).ilike(f"%{clean.lower()}%"),
                )
            )
            .limit(1)
        )
        product = self.db.scalars(stmt).first()
        if product:
            return product

        words = [w.lower() for w in clean.split() if len(w) > 1]
        if words:
            conditions = [func.lower(Product.name).ilike(f"%{w}%") for w in words]
            stmt = (
                select(Product)
                .options(joinedload(Product.inventory))
                .where(*conditions)
                .order_by(Product.rating.desc())
                .limit(1)
            )
            product = self.db.scalars(stmt).first()
            if product:
                return product

        results = self.search(query=clean, limit=1)
        return results[0][0] if results else None

    def search(
        self,
        query: Optional[str] = None,
        query_vector: Optional[List[float]] = None,
        category_slug: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        min_rating: Optional[Decimal] = None,
        limit: int = 10,
        offset: int = 0,
        rrf_k: int = 60,
    ) -> List[Tuple[Product, float]]:
        """Hybrid search combining SQL keyword filtering and pgvector dense similarity with RRF."""
        pool_limit = max(limit * 3, 20)

        # 1. Lexical Filtered Query
        stmt = select(Product).options(joinedload(Product.inventory))
        if query:
            clean = f"%{query.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Product.name).ilike(clean),
                    func.lower(Product.description).ilike(clean),
                    func.lower(Product.brand).ilike(clean),
                    func.lower(Product.category_slug).ilike(clean),
                )
            )
        if category_slug:
            stmt = stmt.where(func.lower(Product.category_slug) == category_slug.strip().lower())
        if brand:
            stmt = stmt.where(func.lower(Product.brand) == brand.strip().lower())
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        if min_rating is not None:
            stmt = stmt.where(Product.rating >= min_rating)

        stmt = stmt.order_by(Product.rating.desc(), Product.review_count.desc()).limit(pool_limit)
        lexical_items = list(self.db.scalars(stmt).unique().all())

        # If no vector provided, return lexical matches directly
        if not query_vector:
            return [(p, 1.0 / (rank + 1)) for rank, p in enumerate(lexical_items[offset : offset + limit])]

        # 2. Vector Search with identical relational filters
        vector_items = []
        try:
            v_stmt = (
                select(Product)
                .options(joinedload(Product.inventory))
                .where(Product.embedding.isnot(None))
            )
            if category_slug:
                v_stmt = v_stmt.where(func.lower(Product.category_slug) == category_slug.strip().lower())
            if brand:
                v_stmt = v_stmt.where(func.lower(Product.brand) == brand.strip().lower())
            if min_price is not None:
                v_stmt = v_stmt.where(Product.price >= min_price)
            if max_price is not None:
                v_stmt = v_stmt.where(Product.price <= max_price)
            if min_rating is not None:
                v_stmt = v_stmt.where(Product.rating >= min_rating)

            v_stmt = v_stmt.order_by(Product.embedding.cosine_distance(query_vector)).limit(pool_limit)
            vector_items = list(self.db.scalars(v_stmt).unique().all())
        except Exception:
            vector_items = []

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[int, float] = {}
        products_by_id: Dict[int, Product] = {}

        for rank, p in enumerate(lexical_items, start=1):
            products_by_id[p.id] = p
            rrf_scores[p.id] = rrf_scores.get(p.id, 0.0) + (1.0 / (rrf_k + rank))

        for rank, p in enumerate(vector_items, start=1):
            products_by_id[p.id] = p
            rrf_scores[p.id] = rrf_scores.get(p.id, 0.0) + (1.0 / (rrf_k + rank))

        fused = sorted(
            [(products_by_id[pid], score) for pid, score in rrf_scores.items()],
            key=lambda x: x[1],
            reverse=True,
        )
        return fused[offset : offset + limit]

    def upsert_product(self, product_data: dict) -> Product:
        existing = self.get_by_slug(product_data["slug"])
        if existing:
            for k, v in product_data.items():
                if hasattr(existing, k) and k not in ("id", "created_at"):
                    setattr(existing, k, v)
            self.db.flush()
            return existing
        new_product = Product(**product_data)
        self.db.add(new_product)
        self.db.flush()
        return new_product
