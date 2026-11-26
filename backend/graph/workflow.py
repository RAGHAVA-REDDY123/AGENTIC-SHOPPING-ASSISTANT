from typing import Any, Dict, Literal, Optional
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from backend.agents.shopping_agent import shopping_agent_node
from backend.graph.state import AgentState
from backend.security.guardrails import (
    ContentFilterMiddleware,
    PIIInputMiddleware,
    PIIOutputMiddleware,
    SafetyGuardrailMiddleware,
)
from backend.services.comparison_service import comparison_pipeline, is_comparison_query
from backend.tools.shopping_tools import ALL_SHOPPING_TOOLS


def input_guardrail_node(state: AgentState) -> Dict[str, Any]:
    """
    Input Guardrail Pipeline:
      - [Layer 1] ContentFilterMiddleware: Blocks prompt injection, jailbreaks, attacks.
      - [Layer 2] PIIInputMiddleware: Tokenizes phone/email into <PII_...> tokens & redacts cards.
    """
    messages = state.get("messages", [])
    if not messages:
        return {}

    human_messages = [m for m in messages if getattr(m, "type", "") in ("human", "user")]
    target_msg = human_messages[-1] if human_messages else messages[-1]
    query = str(getattr(target_msg, "content", ""))

    # Extract previous assistant message for conversational context (e.g. "Which address (reply with 1 or 2)?")
    prev_context = None
    ai_messages = [m for m in messages if getattr(m, "type", "") in ("ai", "assistant")]
    if ai_messages:
        prev_context = str(getattr(ai_messages[-1], "content", ""))

    # [Layer 1] ContentFilterMiddleware
    guard_res = ContentFilterMiddleware.validate(query, context=prev_context)
    if not guard_res.is_safe:
        refusal = guard_res.refusal_message or (
            "I apologize, but I am programmed to assist exclusively with shopping, product specifications, "
            "cart management, and order tracking on this platform."
        )
        return {
            "messages": [AIMessage(content=refusal)],
            "guardrail_blocked": True,
            "guardrail_reason": guard_res.reason,
        }

    # [Layer 2] PIIInputMiddleware: Tokenize user input so Groq never sees real contact info
    tokenized_query = PIIInputMiddleware.process_input(query)
    if tokenized_query != query:
        target_msg.content = tokenized_query

    return {"guardrail_blocked": False}


def route_after_guardrail(
    state: AgentState,
) -> Literal["end", "comparison_pipeline", "shopping_agent"]:
    """
    Routes query based on guardrail status and intent:
      - If blocked by guardrail: Short-circuit directly to END (zero tokens wasted).
      - If comparison intent: Route to regex comparison pipeline.
      - Default: Route to unified shopping agent.
    """
    if state.get("guardrail_blocked", False):
        return "end"

    messages = state.get("messages", [])
    if not messages:
        return "shopping_agent"

    human_messages = [m for m in messages if getattr(m, "type", "") in ("human", "user")]
    target_msg = human_messages[-1] if human_messages else messages[-1]
    query = str(getattr(target_msg, "content", ""))

    if is_comparison_query(query):
        return "comparison_pipeline"

    return "shopping_agent"


def comparison_pipeline_node(state: AgentState) -> Dict[str, Any]:
    messages = state.get("messages", [])
    human_messages = [m for m in messages if getattr(m, "type", "") in ("human", "user")]
    target_msg = human_messages[-1] if human_messages else messages[-1]
    query = str(getattr(target_msg, "content", ""))

    raw_result = comparison_pipeline.run(query)
    # Layer 4 & Layer 5 Output Middlewares
    rehydrated = PIIOutputMiddleware.process_output(raw_result)
    sanitized_result = SafetyGuardrailMiddleware.sanitize_output(rehydrated)
    return {"messages": [AIMessage(content=sanitized_result)]}


def build_shopping_graph(checkpointer: Optional[MemorySaver] = None):
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("input_guardrail", input_guardrail_node)
    workflow.add_node("shopping_agent", shopping_agent_node)
    workflow.add_node("tools", ToolNode(ALL_SHOPPING_TOOLS))
    workflow.add_node("comparison_pipeline", comparison_pipeline_node)

    # Edge from START into Layer 1 Guardrail
    workflow.add_edge(START, "input_guardrail")

    # Guardrail routing: either short-circuits to END or routes to appropriate pipeline
    workflow.add_conditional_edges(
        "input_guardrail",
        route_after_guardrail,
        {
            "end": END,
            "comparison_pipeline": "comparison_pipeline",
            "shopping_agent": "shopping_agent",
        },
    )

    # Tool calling cycle for shopping agent
    workflow.add_conditional_edges(
        "shopping_agent",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )

    workflow.add_edge("tools", "shopping_agent")
    workflow.add_edge("comparison_pipeline", END)

    memory = checkpointer if checkpointer is not None else MemorySaver()
    return workflow.compile(checkpointer=memory)


shopping_workflow = build_shopping_graph()
