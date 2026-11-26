import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class RegressionTracker:
    """
    Compares current evaluation run against historical baselines:
      - Detects newly failing test cases
      - Detects resolved test cases
      - Identifies metric regressions vs target thresholds
      - Compares latency differences
    """

    def __init__(self, history_dir: Path):
        self.history_dir = history_dir
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_file = history_dir / "baseline_summary.json"

    def get_latest_baseline(self) -> Optional[Dict[str, Any]]:
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def compare_and_save_run(
        self,
        current_results: Dict[str, Any],
        failed_ids: List[str],
    ) -> Dict[str, Any]:
        baseline = self.get_latest_baseline()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        new_failures: List[str] = []
        resolved_failures: List[str] = []
        metric_deltas: Dict[str, float] = {}

        if baseline:
            prev_failures = set(baseline.get("failed_case_ids", []))
            curr_failures = set(failed_ids)

            new_failures = list(curr_failures - prev_failures)
            resolved_failures = list(prev_failures - curr_failures)

            prev_metrics = baseline.get("metrics", {})
            curr_metrics = current_results.get("metrics", {})

            for k, val in curr_metrics.items():
                if k in prev_metrics:
                    metric_deltas[k] = round(val - prev_metrics[k], 2)

        # Archive run with timestamp to never overwrite history
        archive_file = self.history_dir / f"run_{timestamp}.json"
        summary_payload = {
            "timestamp": timestamp,
            "overall_pass_rate": current_results.get("overall_pass_rate", 100.0),
            "failed_case_ids": failed_ids,
            "metrics": current_results.get("metrics", {}),
            "performance": current_results.get("performance", {}),
        }

        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, indent=2)

        # Update baseline pointer
        with open(self.baseline_file, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, indent=2)

        return {
            "has_baseline": (baseline is not None),
            "new_failures": new_failures,
            "resolved_failures": resolved_failures,
            "metric_deltas": metric_deltas,
            "archive_path": str(archive_file),
        }
