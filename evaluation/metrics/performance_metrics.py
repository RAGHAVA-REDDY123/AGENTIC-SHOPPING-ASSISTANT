import os
import time
from typing import Any, Dict, List, Optional
import numpy as np


class PerformanceTracker:
    """
    Captures timing, tokens, and cost metrics for agent executions:
      - Average, P50, P95, Max Latency
      - LLM calls per request
      - Input, Output, and Total Tokens
      - Estimated Cost ($ per 1M tokens based on Groq pricing)
      - Tool execution latency & failure rate
    """

    # Estimated Groq pricing (Llama 3.3 70B: ~$0.59 / 1M prompt, ~$0.79 / 1M completion)
    PRICING_PER_MILLION = {
        "prompt": 0.59,
        "completion": 0.79,
    }

    def __init__(self):
        self.latencies_ms: List[float] = []
        self.tool_latencies_ms: List[float] = []
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_llm_calls: int = 0
        self.tool_failures: int = 0
        self.total_tool_calls: int = 0

    def record_latency(self, latency_ms: float):
        self.latencies_ms.append(latency_ms)

    def record_tool_call(self, latency_ms: float, success: bool = True):
        self.total_tool_calls += 1
        self.tool_latencies_ms.append(latency_ms)
        if not success:
            self.tool_failures += 1

    def record_tokens(self, prompt_tokens: int, completion_tokens: int):
        self.total_llm_calls += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

    def get_summary(self) -> Dict[str, Any]:
        lats = self.latencies_ms if self.latencies_ms else [0.0]
        tool_lats = self.tool_latencies_ms if self.tool_latencies_ms else [0.0]

        avg_lat = float(np.mean(lats))
        p50_lat = float(np.percentile(lats, 50))
        p95_lat = float(np.percentile(lats, 95))
        max_lat = float(np.max(lats))

        # Estimated cost
        prompt_cost = (self.total_prompt_tokens / 1_000_000.0) * self.PRICING_PER_MILLION["prompt"]
        comp_cost = (self.total_completion_tokens / 1_000_000.0) * self.PRICING_PER_MILLION["completion"]
        total_cost = prompt_cost + comp_cost

        tool_fail_rate = (self.tool_failures / self.total_tool_calls * 100.0) if self.total_tool_calls > 0 else 0.0

        return {
            "avg_latency_ms": round(avg_lat, 2),
            "p50_latency_ms": round(p50_lat, 2),
            "p95_latency_ms": round(p95_lat, 2),
            "max_latency_ms": round(max_lat, 2),
            "avg_tool_latency_ms": round(float(np.mean(tool_lats)), 2),
            "total_llm_calls": self.total_llm_calls,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "estimated_cost_usd": round(total_cost, 5),
            "tool_failure_rate_pct": round(tool_fail_rate, 2),
            "total_tool_calls": self.total_tool_calls,
        }
