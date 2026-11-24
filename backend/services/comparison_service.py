import asyncio
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.database.connection import get_db_session
from backend.repositories.product_repository import ProductRepository

root_env = Path(__file__).resolve().parents[2] / ".env"
backend_env = Path(__file__).resolve().parents[1] / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env)
elif backend_env.exists():
    load_dotenv(dotenv_path=backend_env)
else:
    load_dotenv()

COMPARISON_PATTERNS = [
    r"\bcompare\s+features\b",
    r"\bcompare\b",
    r"\bcomparison\b",
    r"\bversus\b",
    r"\bvs\.?\b",
    r"\bdifference\s+between\b",
    r"\bwhich\s+(?:is\s+)?better\b",
    r"\bbetter\s+than\b",
    r"\bcompared\s+to\b",
    r"\bin\s+comparison\s+(?:to|with)\b",
]

COMPARISON_REGEX = re.compile("|".join(COMPARISON_PATTERNS), re.IGNORECASE)


def is_comparison_query(query: str) -> bool:
    """Detect product comparison intent using regex patterns."""
    if not query or not isinstance(query, str):
        return False
    return bool(COMPARISON_REGEX.search(query.strip()))


COMPARISON_SYSTEM_PROMPT = """You are an expert product advisor for an e-commerce platform.
Compare the provided products side-by-side using strictly the verified catalog facts and deterministic analysis.

Format your response clearly:
1. Executive Summary & Verdict (who should choose which product)
2. Comparison Table
3. Key Technical Specification Highlights
4. Pricing & Value Analysis (prices in ₹)
5. Pros & Cons for each product

Ground all statements strictly in the provided catalog facts."""


class ComparisonPipeline:
    def __init__(self):
        self._llm: Optional[ChatGroq] = None
        self.fast_patterns = [
            re.compile(r"compare\s+features\s+(?:of\s+)?([^,]+?)\s+(?:and|vs\.?|versus|to)\s+([^,]+?)(?:\?|$)", re.IGNORECASE),
            re.compile(r"(?:compare|comparison)(?:\s+(?:the\s+)?(?:specs|specifications)?(?:\s+(?:of|between|btw))?)?\s+([^,]+?)\s+(?:and|vs\.?|versus|with|to)\s+([^,]+?)(?:\?|$)", re.IGNORECASE),
            re.compile(r"(?:what\s+is\s+the\s+)?difference\s+between\s+([^,]+?)\s+and\s+([^,]+?)(?:\?|$)", re.IGNORECASE),
            re.compile(r"which\s+(?:is\s+better|one\s+to\s+buy)(?:\s+between)?\s+([^,]+?)\s+(?:or|and)\s+([^,]+?)(?:\?|$)", re.IGNORECASE),
            re.compile(r"(?:is\s+)?([^,]+?)\s+better\s+than\s+([^,]+?)(?:\?|$)", re.IGNORECASE),
            re.compile(r"^([^,]+?)\s+(?:vs\.?|versus)\s+([^,]+?)(?:\?|$)", re.IGNORECASE),
            re.compile(r"how\s+does\s+([^,]+?)\s+compare\s+to\s+([^,]+?)(?:\?|$)", re.IGNORECASE),
        ]

    @property
    def llm(self) -> ChatGroq:
        if self._llm is None:
            self._llm = ChatGroq(
                model=os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile"),
                temperature=0.2,
                api_key=os.getenv("GROQ_API_KEY"),
            )
        return self._llm

    def extract_entities(self, query: str) -> Optional[List[str]]:
        """Extract product names via regex patterns, falling back to LLM if needed."""
        text = query.strip()
        for pattern in self.fast_patterns:
            match = pattern.search(text)
            if match:
                item1 = match.group(1).strip()
                item2 = match.group(2).strip()

                trailing = re.split(
                    r"\s+(?:and\s+(?:also\s+)?(?:the|which|add|tell|show|put|buy)|which|please)",
                    item2,
                    flags=re.IGNORECASE,
                )
                if trailing and trailing[0].strip():
                    item2 = trailing[0].strip()

                item1 = re.sub(r"^(?:the\s+)", "", item1, flags=re.IGNORECASE).strip()
                item2 = re.sub(r"^(?:the\s+)", "", item2, flags=re.IGNORECASE).strip()

                if item1 and item2:
                    return [item1, item2]

        try:
            prompt = (
                "Extract exactly 2 product names being compared in this query. "
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
                "slug": product.slug,
                "brand": product.brand,
                "category": product.category_slug,
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
        with ThreadPoolExecutor(max_workers=min(max(len(entities), 1), 4)) as executor:
            results = list(executor.map(self._fetch_single_product, entities))
        return [r for r in results if r is not None]

    async def afetch_products_parallel(self, entities: List[str]) -> List[Dict[str, Any]]:
        tasks = [asyncio.to_thread(self._fetch_single_product, entity) for entity in entities]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    def compare_attributes_deterministically(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform structured attribute comparison and build a markdown table."""
        if len(products) < 2:
            return {"error": "Need at least 2 products for comparison"}

        p1, p2 = products[0], products[1]

        price_diff = abs(p1["price"] - p2["price"])
        if p1["price"] < p2["price"]:
            price_adv = f"{p1['name']} is cheaper by ₹{price_diff:,.2f}"
        elif p2["price"] < p1["price"]:
            price_adv = f"{p2['name']} is cheaper by ₹{price_diff:,.2f}"
        else:
            price_adv = "Identical pricing"

        rating_diff = abs(p1["rating"] - p2["rating"])
        if p1["rating"] > p2["rating"]:
            rating_adv = f"{p1['name']} leads by {rating_diff:.1f} stars"
        elif p2["rating"] > p1["rating"]:
            rating_adv = f"{p2['name']} leads by {rating_diff:.1f} stars"
        else:
            rating_adv = "Equal rating"

        discount_diff = abs(p1["discount_percent"] - p2["discount_percent"])
        if p1["discount_percent"] > p2["discount_percent"]:
            discount_adv = f"{p1['name']} has {discount_diff}% higher discount"
        elif p2["discount_percent"] > p1["discount_percent"]:
            discount_adv = f"{p2['name']} has {discount_diff}% higher discount"
        else:
            discount_adv = "Equal discount"

        all_spec_keys = list(dict.fromkeys(list(p1["specifications"].keys()) + list(p2["specifications"].keys())))
        all_feature_keys = list(dict.fromkeys(list(p1["features"].keys()) + list(p2["features"].keys())))

        table_lines = [
            f"| Attribute / Specification | {p1['name']} | {p2['name']} | Comparison / Advantage |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Brand** | {p1['brand']} | {p2['brand']} | - |",
            f"| **Price** | ₹{p1['price']:,.2f} | ₹{p2['price']:,.2f} | {price_adv} |",
            f"| **Original Price** | ₹{p1['original_price']:,.2f} | ₹{p2['original_price']:,.2f} | - |",
            f"| **Discount** | {p1['discount_percent']}% | {p2['discount_percent']}% | {discount_adv} |",
            f"| **Rating** | {p1['rating']}/5.0 ({p1['review_count']} reviews) | {p2['rating']}/5.0 ({p2['review_count']} reviews) | {rating_adv} |",
            f"| **Availability** | {'In Stock (' + str(p1['stock_quantity']) + ')' if p1['in_stock'] else 'Out of Stock'} | {'In Stock (' + str(p2['stock_quantity']) + ')' if p2['in_stock'] else 'Out of Stock'} | - |",
        ]

        for key in all_feature_keys:
            val1 = p1["features"].get(key, "N/A")
            val2 = p2["features"].get(key, "N/A")
            table_lines.append(f"| **{key}** | {val1} | {val2} | - |")

        for key in all_spec_keys:
            val1 = p1["specifications"].get(key, "N/A")
            val2 = p2["specifications"].get(key, "N/A")
            table_lines.append(f"| **{key}** | {val1} | {val2} | - |")

        return {
            "price_advantage": price_adv,
            "rating_advantage": rating_adv,
            "discount_advantage": discount_adv,
            "markdown_table": "\n".join(table_lines),
        }

    def _format_spec_sheet(self, products: List[Dict[str, Any]]) -> str:
        blocks = []
        for p in products:
            stock_info = f"In Stock ({p['stock_quantity']} units)" if p["in_stock"] else "Out of Stock"
            block = (
                f"### {p['name']} (Brand: {p['brand']})\n"
                f"- Price: ₹{p['price']:,.2f} (Original: ₹{p['original_price']:,.2f}, {p['discount_percent']}% off)\n"
                f"- Rating: {p['rating']}/5.0 ({p['review_count']:,} verified reviews)\n"
                f"- Inventory Status: {stock_info}\n"
                f"- Key Features: {json.dumps(p['features'])}\n"
                f"- Technical Specifications: {json.dumps(p['specifications'])}"
            )
            blocks.append(block)
        return "\n\n".join(blocks)

    def run(self, query: str, entities: Optional[List[str]] = None) -> str:
        if not entities:
            entities = self.extract_entities(query)

        if not entities or len(entities) < 2:
            return "Please specify two products to compare (e.g. 'compare ASUS ROG Strix G15 vs Apple MacBook Pro 14 M3')."

        products = self.fetch_products_parallel(entities)

        if len(products) < 2:
            if products:
                return f"I found **{products[0]['name']}**, but could not find the second item ('{entities[1]}') in the catalog."
            return f"I could not find matching products in the catalog for '{entities[0]}' and '{entities[1]}'."

        analysis = self.compare_attributes_deterministically(products)
        spec_sheet = self._format_spec_sheet(products)
        comparison_table = analysis.get("markdown_table", "")

        try:
            messages = [
                SystemMessage(content=COMPARISON_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"User Query: {query}\n\n"
                        f"Deterministic Comparison:\n"
                        f"- {analysis.get('price_advantage')}\n"
                        f"- {analysis.get('rating_advantage')}\n"
                        f"- {analysis.get('discount_advantage')}\n\n"
                        f"Structured Comparison Table:\n{comparison_table}\n\n"
                        f"Catalog Specifications:\n{spec_sheet}"
                    )
                ),
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return (
                f"### Product Comparison: {products[0]['name']} vs {products[1]['name']}\n\n"
                f"- {analysis.get('price_advantage')}\n"
                f"- {analysis.get('rating_advantage')}\n"
                f"- {analysis.get('discount_advantage')}\n\n"
                f"{comparison_table}\n\n"
                f"*(Note: Summary synthesis unavailable: {e})*"
            )


comparison_pipeline = ComparisonPipeline()

__all__ = [
    "is_comparison_query",
    "ComparisonPipeline",
    "comparison_pipeline",
]
