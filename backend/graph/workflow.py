
from typing import Literal, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from backend.agents.supervisor import supervisor_node
from backend.agents.discovery_agent import discovery_agent_node
from backend.agents.comparison_agent import comparison_agent_node
from backend.agents.cart_agent import cart_agent_node

from backend.graph.state import AgentState

from backend.tools.discovery_tools import DISCOVERY_TOOLS
from backend.tools.cart_tools import CART_TOOLS


def route_supervisor(
    state: AgentState,
) -> Literal[
    "discovery_agent",
    "comparison_agent",
    "cart_agent",
    "__end__",
]:
    next_node = state.get("next", "FINISH")

    if next_node in (
        "discovery_agent",
        "comparison_agent",
        "cart_agent",
    ):
        return next_node

    return END


def route_after_discovery(
    state: AgentState,
) -> Literal["comparison_agent", "cart_agent", "__end__"]:

    next_node = state.get("next", "FINISH")

    if next_node in ("comparison_agent", "cart_agent"):
        return next_node

    return END


def route_after_comparison(
    state: AgentState,
) -> Literal["cart_agent", "__end__"]:

    next_node = state.get("next", "FINISH")

    if next_node == "cart_agent":
        return "cart_agent"

    return END


def build_shopping_graph(
    checkpointer: Optional[MemorySaver] = None,
):
    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("supervisor", supervisor_node)

    workflow.add_node("discovery_agent", discovery_agent_node)
    workflow.add_node("discovery_tools", ToolNode(DISCOVERY_TOOLS))

    workflow.add_node("comparison_agent", comparison_agent_node)

    workflow.add_node("cart_agent", cart_agent_node)
    workflow.add_node("cart_tools", ToolNode(CART_TOOLS))

    # Entry point
    workflow.add_edge(START, "supervisor")

    # Initial routing
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "discovery_agent": "discovery_agent",
            "comparison_agent": "comparison_agent",
            "cart_agent": "cart_agent",
            END: END,
        },
    )

    # Discovery agent -> tools or next specialist
    workflow.add_conditional_edges(
        "discovery_agent",
        tools_condition,
        {
            "tools": "discovery_tools",
            END: "discovery_router",
        },
    )

    workflow.add_node(
        "discovery_router",
        lambda state: {},
    )

    workflow.add_conditional_edges(
        "discovery_router",
        route_after_discovery,
        {
            "comparison_agent": "comparison_agent",
            "cart_agent": "cart_agent",
            END: END,
        },
    )

    workflow.add_edge("discovery_tools", "discovery_agent")

    # Comparison agent -> cart or END
    workflow.add_conditional_edges(
        "comparison_agent",
        route_after_comparison,
        {
            "cart_agent": "cart_agent",
            END: END,
        },
    )

    # Cart agent -> tools or END
    workflow.add_conditional_edges(
        "cart_agent",
        tools_condition,
        {
            "tools": "cart_tools",
            END: END,
        },
    )

    workflow.add_edge("cart_tools", "cart_agent")

    # Compile
    memory = checkpointer if checkpointer is not None else MemorySaver()

    return workflow.compile(checkpointer=memory)


shopping_workflow = build_shopping_graph()
