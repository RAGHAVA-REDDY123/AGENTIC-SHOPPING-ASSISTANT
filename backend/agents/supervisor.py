import os
from typing import Any, Dict, List, Literal, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_groq import ChatGroq

load_dotenv()

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor Orchestrator for an e-commerce assistant.
Your job is to manage the flow of conversation between specialist agents to satisfy the customer's request.

Available Specialists:
1. `discovery_agent`: Handles product discovery, catalog search, recommendations, detailed specifications, and physical stock checks. Also handles greetings and general shopping advice.
2. `comparison_agent`: Handles side-by-side technical and price comparisons between products.
3. `cart_agent`: Handles shopping cart actions (adding items to cart, removing items, viewing cart total, clearing cart).

Routing Guidelines:
- If the customer wants to compare products: route to `comparison_agent`.
- If the customer wants to search, explore, check stock, or ask general shopping questions: route to `discovery_agent`.
- If the customer wants to add, remove, view, or clear their cart: route to `cart_agent`.
- For compound requests (e.g. "compare X and Y and add the winner to cart"):
  - If comparison is not yet done: route to `comparison_agent`.
  - Once comparison is completed and an item still needs to be added to cart: route to `cart_agent`.
- CRITICAL: Route to `FINISH` once the customer's full request has been addressed and no pending actions remain."""


class SupervisorDecision(BaseModel):
    next_agent: Literal["discovery_agent", "comparison_agent", "cart_agent", "FINISH"] = Field(
        description="The next specialist agent to call, or FINISH if the user request is satisfied."
    )
    reasoning: Optional[str] = Field(description="Brief reason for routing choice.")


llm = ChatGroq(
    model=os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b"),
    temperature=0.0,
    api_key=os.getenv("GROQ_API_KEY"),
).with_structured_output(SupervisorDecision)


def supervisor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    messages: List[BaseMessage] = list(state.get("messages", []))
    prompt_messages = [SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT)] + messages
    decision: SupervisorDecision = llm.invoke(prompt_messages)
    return {"next": decision.next_agent}