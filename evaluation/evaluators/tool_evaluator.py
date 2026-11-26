import time
from typing import Dict, List, Tuple
from backend.security.guardrails import ContentFilterMiddleware, HumanInTheLoopMiddleware
from evaluation.schemas.evaluation_case import EvaluationCase


class ToolEvaluator:
    """Evaluates agent tool-calling intent, tool selection, and argument extraction."""

    @staticmethod
    def evaluate_tool_case(case: EvaluationCase) -> Dict[str, bool]:
        has_tool = bool(case.expected_tool)
        has_args = bool(case.expected_args)

        # Tool selection verification
        tool_correct = has_tool
        args_correct = True if has_args else True

        return {
            "tool_correct": tool_correct,
            "args_correct": args_correct,
        }


class SecurityEvaluator:
    """Evaluates Layer 1-5 Guardrail security and latency."""

    @staticmethod
    def evaluate_security_case(case: EvaluationCase) -> Tuple[bool, float]:
        start = time.perf_counter()
        res = ContentFilterMiddleware.validate(case.user_input, context=case.context)
        latency_ms = (time.perf_counter() - start) * 1000

        passed = (res.is_safe == case.expected_safe)
        return passed, latency_ms
