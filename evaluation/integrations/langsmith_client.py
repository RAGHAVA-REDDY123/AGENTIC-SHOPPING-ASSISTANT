import os
from typing import Any, Dict, Optional


class LangSmithIntegration:
    """
    Manages LangSmith tracing instrumentation for agent evaluation runs:
      - Uses existing LANGCHAIN_TRACING_V2 configuration
      - Associates evaluation metadata with trace sessions
      - Avoids duplicate client instantiation
    """

    @staticmethod
    def is_enabled() -> bool:
        return os.getenv("LANGCHAIN_TRACING_V2", "false").lower() in ("true", "1", "yes")

    @classmethod
    def get_run_metadata(cls, test_id: str, category: str) -> Dict[str, Any]:
        return {
            "evaluation_case_id": test_id,
            "category": category,
            "tracing_enabled": cls.is_enabled(),
            "project_name": os.getenv("LANGCHAIN_PROJECT", "agentic-shopping-assistant"),
        }
