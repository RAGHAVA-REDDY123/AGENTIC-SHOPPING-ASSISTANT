from typing import Any, Dict, Literal, Optional
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from backend.agents.shopping_agent import shopping_agent_node
from backend.graph.state import AgentState
from backend.services.comparison_service import comparison_pipeline, is_comparison_query
from backend.tools.shopping_tools import ALL_SHOPPING_TOOLS


def route_query_intent(state: AgentState) -> Literal["comparison_pipeline", "shopping_agent"]:
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

    result = comparison_pipeline.run(query)
    return {"messages": [AIMessage(content=result)]}


def build_shopping_graph(checkpointer: Optional[MemorySaver] = None):
    workflow = StateGraph(AgentState)

    workflow.add_node("shopping_agent", shopping_agent_node)
    workflow.add_node("tools", ToolNode(ALL_SHOPPING_TOOLS))
    workflow.add_node("comparison_pipeline", comparison_pipeline_node)

    workflow.add_conditional_edges(
        START,
        route_query_intent,
        {
            "comparison_pipeline": "comparison_pipeline",
            "shopping_agent": "shopping_agent",
        },
    )

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
