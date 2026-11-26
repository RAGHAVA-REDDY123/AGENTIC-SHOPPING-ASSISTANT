from typing import Dict, Any, List
from backend.services.comparison_service import is_comparison_query
from backend.security.guardrails import ContentFilterMiddleware
from evaluation.schemas.evaluation_case import WorkflowCase


class WorkflowEvaluator:
    """Evaluates multi-step multi-turn purchase and comparison workflows."""

    @staticmethod
    def evaluate_workflow(session: WorkflowCase) -> Dict[str, Any]:
        turns = session.turns
        all_passed = True
        prev_context = None

        for turn in turns:
            context = turn.context or prev_context
            guard_res = ContentFilterMiddleware.validate(turn.user_input, context=context)

            if not guard_res.is_safe:
                all_passed = False
                break

            if turn.expected_route == "comparison_pipeline":
                if not is_comparison_query(turn.user_input):
                    all_passed = False
                    break

            prev_context = f"Assistant processed turn {turn.turn} successfully"

        return {
            "session_id": session.id,
            "session_name": session.session_name,
            "total_turns": len(turns),
            "workflow_passed": all_passed,
        }
