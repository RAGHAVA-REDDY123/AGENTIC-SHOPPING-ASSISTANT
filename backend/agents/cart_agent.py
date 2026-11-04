import os
from typing import Any, Dict, List
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.tools.cart_tools import CART_TOOLS

load_dotenv()

CART_AGENT_SYSTEM_PROMPT = """You are a Shopping Cart Specialist for an e-commerce platform.
Your mission is to manage the customer's shopping cart reliably and accurately.

### OPERATING RULES:
1. CART ACTIONS:
   - Use `add_to_cart` to add requested items with requested quantities.
   - Use `remove_from_cart` to remove items.
   - Use `clear_cart` when the customer wants to empty or clear their cart.
   - Use `get_cart` to display the active cart items and calculate totals.
2. ACCURACY:
   - Never invent or assume cart totals or stock levels.
   - Report cart contents clearly, referencing item names, quantities, and prices in Indian Rupees (₹)."""

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b"),
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY"),
).bind_tools(CART_TOOLS)


def cart_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    messages: List[BaseMessage] = list(state.get("messages", []))

    # ------------------------------------------------------------
    # Optimization: if the most recent message is the result of the
    # `get_cart` tool we just return it directly – no extra LLM call.
    # ------------------------------------------------------------
    from langchain_core.messages import ToolMessage
    if messages and isinstance(messages[-1], ToolMessage) and messages[-1].name == "get_cart":
        # The tool already returned a nicely formatted JSON/string of the cart.
        # Propagate it as the final response without invoking the LLM again.
        return {"messages": [messages[-1]]}
    # ------------------------------------------------------------
    # Normal path – prepend system prompt and let the LLM decide what to do.
    # ------------------------------------------------------------
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=CART_AGENT_SYSTEM_PROMPT)] + messages
    else:
        messages[0] = SystemMessage(content=CART_AGENT_SYSTEM_PROMPT)

    response = llm.invoke(messages)
    return {"messages": [response]}
    messages: List[BaseMessage] = list(state.get("messages", []))

    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=CART_AGENT_SYSTEM_PROMPT)] + messages
    else:
        messages[0] = SystemMessage(content=CART_AGENT_SYSTEM_PROMPT)

    response = llm.invoke(messages)
    return {"messages": [response]}

