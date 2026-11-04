import os
from typing import Any, Dict, List
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.tools.discovery_tools import DISCOVERY_TOOLS

load_dotenv()

DISCOVERY_AGENT_SYSTEM_PROMPT = """You are a Product Discovery Specialist for an e-commerce platform.
Your mission is to help customers discover products, explore detailed specifications, and check real-time stock availability.

### OPERATING RULES:
1. STRICT GROUNDING IN FACTS:
   - All product facts, pricing, ratings, and stock levels must come directly from tool outputs.
   - NEVER invent or hallucinate products, discounts, or specifications.
2. RECOMMENDATIONS:
   - Explain the ranking criteria (rating, verified reviews, discount) provided by search results.
3. CONVERSATIONAL TONE:
   - Be helpful, concise, and professional. Reference prices accurately in Indian Rupees (₹)."""

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b"),
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY"),
).bind_tools(DISCOVERY_TOOLS)


def discovery_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    messages: List[BaseMessage] = list(state.get("messages", []))

    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=DISCOVERY_AGENT_SYSTEM_PROMPT)] + messages
    else:
        messages[0] = SystemMessage(content=DISCOVERY_AGENT_SYSTEM_PROMPT)

    response = llm.invoke(messages)
    return {"messages": [response]}

