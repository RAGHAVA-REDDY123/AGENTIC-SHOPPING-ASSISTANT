import os
from pathlib import Path
from dotenv import load_dotenv

EVAL_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = EVAL_ROOT.parent

load_dotenv(PROJECT_ROOT / ".env")

DATASETS_DIR = EVAL_ROOT / "datasets"
REPORTS_DIR = EVAL_ROOT / "reports" / "results"

TARGET_THRESHOLDS = {
    "tool_selection_accuracy": 0.95,
    "tool_argument_accuracy": 0.98,
    "workflow_success_rate": 0.95,
    "product_retrieval_precision_at_5": 0.85,
    "response_groundedness": 0.90,
    "critical_cart_stock_correctness": 1.00,
    "regression_test_pass_rate": 1.00,
}
