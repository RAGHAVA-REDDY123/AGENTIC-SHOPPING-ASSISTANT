from typing import Any, Dict
from langchain_core.messages import AIMessage

from backend.services.comparison_service import comparison_pipeline


def comparison_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    human_messages = [m for m in state.get("messages", []) if getattr(m, "type", "") == "human"]
    target_msg = human_messages[-1] if human_messages else state["messages"][-1]
    query = str(target_msg.content)
    entities = comparison_pipeline.extract_entities(query) or []
    comparison_result = comparison_pipeline.run(query, entities)
    return {"messages": [AIMessage(content=comparison_result)]}

