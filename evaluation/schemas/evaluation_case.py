from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    """Production evaluation case schema with full ground truth and criteria."""

    id: str = Field(..., description="Unique case identifier (e.g. SRCH-01, SEC-02)")
    category: str = Field(..., description="Test category name")
    description: str = Field(..., description="Short explanation of scenario")
    user_input: str = Field(..., description="User query or attack string")
    context: Optional[str] = Field(None, description="Previous assistant message for conversational context")
    expected_intent: Optional[str] = Field(None, description="Classified intent (search, details, cart, checkout, compare, etc.)")
    expected_tool: Optional[str] = Field(None, description="Expected shopping tool name")
    expected_args: Dict[str, Any] = Field(default_factory=dict, description="Expected tool parameters")
    expected_product_ids: List[int] = Field(default_factory=list, description="Ground truth product IDs for relevance")
    expected_safe: bool = Field(True, description="Whether the request is safe and in-scope")
    expected_layer: Optional[str] = Field(None, description="Expected defense layer (deterministic_regex, interactive_whitelist, semantic_llm)")
    expected_business_outcome: Optional[str] = Field(None, description="Expected database or transactional outcome")
    evaluation_criteria: Optional[str] = Field(None, description="Rules determining test pass/fail")
    ground_truth_claims: List[str] = Field(default_factory=list, description="Ground truth claims for RAG review checks")
    negative_hallucinations: List[str] = Field(default_factory=list, description="Hallucinated statements that must not appear")


class TurnCase(BaseModel):
    turn: int
    user_input: str
    expected_tool: Optional[str] = None
    expected_args: Dict[str, Any] = Field(default_factory=dict)
    expected_route: Optional[str] = None
    context: Optional[str] = None
    expected_business_outcome: Optional[str] = None


class WorkflowCase(BaseModel):
    id: str
    category: str = "multi_step_workflows"
    session_name: str
    description: str
    turns: List[TurnCase]


class MetricResult(BaseModel):
    name: str
    passed: int
    total: int
    target: str
    score_pct: float
    status: str
    latency_ms: Optional[float] = None
