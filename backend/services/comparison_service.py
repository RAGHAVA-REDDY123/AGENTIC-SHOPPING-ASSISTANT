import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.database.connection import get_db_session
from backend.repositories.product_repository import ProductRepository

load_dotenv()

COMPARISON_SYSTEM_PROMPT = """You are an expert product advisor for an e-commerce platform.
Compare the following products side-by-side using ONLY the provided verified catalog specifications.

Format your response clearly with:
1. Executive Summary & Verdict (who should buy which product)
2. Key Specifications Comparison (Display, Processor/Performance, Cameras, Battery/Charging, Build)
3. Pricing & Value Analysis (Current prices in ₹, discounts, value proposition)
4. Pros & Cons for each product

Ground all statements strictly in the provided catalog facts. Do not invent specs or prices."""


class ComparisonPipeline:
    def __init__(self):
        self.llm = ChatGroq(
            model=os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b"),
            temperature=0.2,
            api_key=os.getenv("GROQ_API_KEY"),
        )
        self.fast_patterns = [
            re.compile(r"(?:compare|comparison)(?:\s+(?:the\s+)?(?:specs|specifications)?(?:\s+(?:of|between|btw))?)?\s+([^,]+?)\s+(?:and|vs\.?|versus|with|to)\s+([^,]+?)(?:\?|$)", re.IGNORECASE),
            re.compile(r"(?:what\s+is\s+the\s+)?difference\s+between\s+([^,]+?)\s+and\s+([^,]+?)(?:\?|$)", re.IGNORECASE),
            re.compile(r"^([^,]+?)\s+(?:vs\.?|versus)\s+([^,]+?)(?:\?|$)", re.IGNORECASE),
            re.compile(r"which\s+(?:is\s+better|one\s+to\s+buy)(?:\s+between)?\s+([^,]+?)\s+(?:or|and)\s+([^,]+?)(?:\?|$)", re.IGNORECASE),
        ]

    def extract_entities(self, query: str) -> Optional[List[str]]:
        text = query.strip()
        for pattern in self.fast_patterns:
            match = pattern.search(text)
            if match:
                item1 = match.group(1).strip()
                item2 = match.group(2).strip()

                # Clean trailing clauses from item2 if present
                trailing = re.split(
                    r"\s+(?:and\s+(?:also\s+)?(?:the|which|add|tell|show|put|buy)|which|please)",
                    item2,
                    flags=re.IGNORECASE,
                )
                if trailing and trailing[0].strip():
                    item2 = trailing[0].strip()

                if item1 and item2:
                    return [item1, item2]

        try:
            prompt = (
                "Extract exactly 2 product names being compared in this user query. "
                "Ignore any instructions about carts, questions, or actions. "
                "Return ONLY a JSON array of 2 strings: [\"Product 1\", \"Product 2\"]. "
                f"Query: {text}"
            )
            res = self.llm.invoke([HumanMessage(content=prompt)]).content.strip()
            match = re.search(r"\[.*?\]", res, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, list) and len(parsed) >= 2:
                    return [str(p).strip() for p in parsed[:2]]
        except Exception:
            pass

        return None

    def _fetch_single_product(self, name_or_keyword: str) -> Optional[Dict[str, Any]]:
        with get_db_session() as db:
            repo = ProductRepository(db)
            product = repo.find_by_name_or_keyword(name_or_keyword)
            if not product:
                return None

            stock = (product.inventory.stock_quantity - product.inventory.reserved_quantity) if product.inventory else 0
            return {
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "price": float(product.price),
                "original_price": float(product.original_price),
                "discount_percent": product.discount_percent,
                "rating": float(product.rating),
                "review_count": product.review_count,
                "in_stock": stock > 0,
                "stock_quantity": stock,
                "features": product.features or {},
                "specifications": product.specifications or {},
            }

    def fetch_products_parallel(self, entities: List[str]) -> List[Dict[str, Any]]:
        with ThreadPoolExecutor(max_workers=min(len(entities), 4)) as executor:
            results = list(executor.map(self._fetch_single_product, entities))
        return [r for r in results if r is not None]

    def _format_spec_sheet(self, products: List[Dict[str, Any]]) -> str:
        blocks = []
        for p in products:
            stock_info = f"In Stock ({p['stock_quantity']} units)" if p["in_stock"] else "Out of Stock"
            block = (
                f"### {p['name']} (Brand: {p['brand']})\n"
                f"- Price: ₹{p['price']:,.2f} (Original: ₹{p['original_price']:,.2f}, {p['discount_percent']}% off)\n"
                f"- Rating: {p['rating']}/5.0 ({p['review_count']:,} verified reviews)\n"
                f"- Inventory Status: {stock_info}\n"
                f"- Key Features: {json.dumps(p['features'], indent=2)}\n"
                f"- Technical Specifications: {json.dumps(p['specifications'], indent=2)}"
            )
            blocks.append(block)
        return "\n\n".join(blocks)

    def run(self, query: str, entities: List[str]) -> str:
        products = self.fetch_products_parallel(entities)

        if len(products) < 2:
            if products:
                return (
                    f"I found **{products[0]['name']}**, but I could not find the second item "
                    "in our catalog to complete the comparison."
                )
            return (
                f"I could not find matching products in our catalog for '{entities[0]}' and "
                f"'{entities[1]}' to compare."
            )

        spec_sheet = self._format_spec_sheet(products)
        messages = [
            SystemMessage(content=COMPARISON_SYSTEM_PROMPT),
            HumanMessage(content=f"User Query: {query}\n\nVerified Catalog Data:\n{spec_sheet}"),
        ]
        response = self.llm.invoke(messages)
        return response.content


comparison_pipeline = ComparisonPipeline()

