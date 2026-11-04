from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, description="Product display name")
    slug: str = Field(..., min_length=1, description="Unique URL-friendly slug")
    description: Optional[str] = Field(None, description="Detailed product description")
    features: Dict[str, Any] = Field(default_factory=dict, description="Structured feature dictionary")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Structured technical specifications")
    price: Decimal = Field(..., gt=Decimal("0.00"), description="Selling price (Decimal)")
    original_price: Decimal = Field(..., gt=Decimal("0.00"), description="Original or reference price")
    discount_percent: int = Field(default=0, ge=0, le=100, description="Discount percentage between 0 and 100")
    brand: str = Field(..., min_length=1, description="Brand name")
    category_slug: str = Field(..., min_length=1, description="Category slug (e.g. laptops, mobiles)")
    tags: List[str] = Field(default_factory=list, description="Searchable tag keywords")
    rating: Decimal = Field(default=Decimal("0.0"), ge=Decimal("0.0"), le=Decimal("5.0"), description="Rating between 0.0 and 5.0")
    review_count: int = Field(default=0, ge=0, description="Non-negative number of customer reviews")
    image_url: Optional[str] = Field(None, description="Product image URL")
    embedding: Optional[List[float]] = Field(None, description="384-dimensional dense semantic vector")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean:
            raise ValueError("Slug cannot be blank")
        return clean


class ProductCreate(ProductBase):
    """Schema for validating products to be inserted into the catalog."""
    initial_stock: Optional[int] = Field(default=10, ge=0, description="Initial inventory stock to seed")


class ProductRead(ProductBase):
    """Schema for serialized product catalog responses."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    stock_quantity: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ProductSearchParams(BaseModel):
    """Search and filter criteria for the product catalog."""
    query: Optional[str] = None
    category_slug: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_rating: Optional[Decimal] = None
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)


class InventoryCheckResult(BaseModel):
    """Structured response for stock availability checks."""
    product_id: int
    product_name: str
    is_available: bool
    stock_quantity: int
    requested_quantity: int
    status: str  # in_stock, low_stock, out_of_stock, insufficient_quantity
    message: str


class CartItemRead(BaseModel):
    """Cart item breakdown with price calculation."""
    id: int
    product_id: int
    product_name: str
    product_slug: str
    brand: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CartRead(BaseModel):
    """Full cart summary with computed totals."""
    id: int
    customer_id: str
    items: List[CartItemRead] = Field(default_factory=list)
    total_items: int = 0
    total_price: Decimal = Decimal("0.00")
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CartActionResponse(BaseModel):
    """Response returned by cart modification operations."""
    success: bool
    action: str
    message: str
    cart: Optional[CartRead] = None
