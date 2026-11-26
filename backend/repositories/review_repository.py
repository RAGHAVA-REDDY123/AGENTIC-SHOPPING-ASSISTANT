from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.product import ProductReview


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_reviews_for_product(
        self,
        product_id: int,
        focus: Optional[str] = None,
        query_vector: Optional[List[float]] = None,
        limit: int = 3,
    ) -> List[ProductReview]:
        stmt = select(ProductReview).where(ProductReview.product_id == product_id)
        clean_focus = (focus or "").strip().lower()

        if clean_focus in ("best", "positive", "top"):
            stmt = stmt.where(ProductReview.rating >= 4).order_by(
                ProductReview.helpful_votes.desc(), ProductReview.rating.desc()
            )
            return list(self.db.scalars(stmt.limit(limit)).all())

        if clean_focus in ("worst", "critical", "negative", "complaints"):
            stmt = stmt.where(ProductReview.rating <= 3).order_by(
                ProductReview.helpful_votes.desc(), ProductReview.rating.asc()
            )
            return list(self.db.scalars(stmt.limit(limit)).all())

        if query_vector:
            stmt = (
                stmt.where(ProductReview.embedding.isnot(None))
                .order_by(ProductReview.embedding.cosine_distance(query_vector))
                .limit(limit)
            )
            return list(self.db.scalars(stmt).all())

        pos_stmt = (
            select(ProductReview)
            .where(ProductReview.product_id == product_id, ProductReview.rating >= 4)
            .order_by(ProductReview.helpful_votes.desc())
            .limit(2)
        )
        neg_stmt = (
            select(ProductReview)
            .where(ProductReview.product_id == product_id, ProductReview.rating <= 3)
            .order_by(ProductReview.helpful_votes.desc())
            .limit(1)
        )
        pos = list(self.db.scalars(pos_stmt).all())
        neg = list(self.db.scalars(neg_stmt).all())
        return pos + neg

    def add_review(
        self,
        product_id: int,
        author_name: str,
        rating: int,
        title: str,
        comment: str,
        helpful_votes: int = 0,
        verified_purchase: bool = True,
        embedding: Optional[List[float]] = None,
    ) -> ProductReview:
        review = ProductReview(
            product_id=product_id,
            author_name=author_name,
            rating=rating,
            title=title,
            comment=comment,
            helpful_votes=helpful_votes,
            verified_purchase=verified_purchase,
            embedding=embedding,
        )
        self.db.add(review)
        self.db.flush()
        return review

