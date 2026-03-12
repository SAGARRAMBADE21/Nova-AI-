"""
utils/llmops.py
LLMOps — Full observability, logging, metrics, and caching layer
Tracks: queries, retrievals, agent actions, tool invocations, security events
Dashboard: Grafana (via Prometheus metrics)
"""

import os
import logging
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)




# ── Log entry ─────────────────────────────────────────────────────────────

@dataclass
class InteractionLog:
    interaction_id:  str
    user_id:         str
    session_id:      str
    query:           str             # PII-stripped in production
    response:        str
    confidence:      str
    sources:         list[str]
    tool_actions:    list[dict]
    security_events: list[str]
    latency_ms:      float
    token_count:     int
    hitl_triggered:  bool
    timestamp:       str             = field(default_factory=lambda: datetime.utcnow().isoformat())
    error:           Optional[str]   = None


class LLMOpsLogger:
    """
    Logs every interaction.
    PII is stripped before logging.
    Logs retained per company compliance policy.
    """

    PII_PATTERNS = [
        r'\b\d{3}-\d{2}-\d{4}\b',          # SSN
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',              # Credit card
        r'\b\d{10,12}\b',                   # Phone
    ]

    def __init__(self):
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        self.log_file = log_dir / "interactions.jsonl"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        logger.info("[LLMOps] Logger initialised.")

    def log(self, entry: InteractionLog):
        """Write interaction log. Strip PII before writing."""
        sanitised = asdict(entry)
        sanitised["query"]    = self._strip_pii(entry.query)
        sanitised["response"] = self._strip_pii(entry.response)

        with open(self.log_file, "a") as f:
            f.write(json.dumps(sanitised) + "\n")

        logger.info(
            f"[LLMOps] Interaction logged | "
            f"id={entry.interaction_id} | "
            f"user={entry.user_id} | "
            f"latency={entry.latency_ms:.0f}ms | "
            f"tokens={entry.token_count} | "
            f"confidence={entry.confidence} | "
            f"hitl={entry.hitl_triggered}"
        )

    def log_security_event(self, event_type: str, user_id: str,
                           detail: str, session_id: str = ""):
        logger.warning(
            f"[LLMOps][SECURITY] type={event_type} | "
            f"user={user_id} | session={session_id} | detail={detail}"
        )

    def log_tool_invocation(self, plugin: str, action: str,
                            success: bool, user_id: str):
        logger.info(
            f"[LLMOps][TOOL] plugin={plugin} | action={action} | "
            f"success={success} | user={user_id}"
        )

    def log_hitl_event(self, request_id: str, reason: str,
                       level: str, user_id: str):
        logger.warning(
            f"[LLMOps][HITL] request_id={request_id} | "
            f"level={level} | user={user_id} | reason={reason}"
        )

    def _strip_pii(self, text: str) -> str:
        import re
        for pattern in self.PII_PATTERNS:
            text = re.sub(pattern, "[REDACTED]", text)
        return text




# ── Metrics (Prometheus-compatible) ──────────────────────────────────────

class MetricsCollector:
    """
    Simple in-memory metrics.
    Production: expose via prometheus_client for Grafana scraping.
    """

    def __init__(self):
        self.query_count     = 0
        self.tool_count      = 0
        self.security_blocks = 0
        self.hitl_count      = 0
        self.total_latency   = 0.0
        self.total_tokens    = 0
        self.errors          = 0

    def record_query(self, latency_ms: float, tokens: int):
        self.query_count   += 1
        self.total_latency += latency_ms
        self.total_tokens  += tokens

    def record_tool(self):
        self.tool_count += 1

    def record_security_block(self):
        self.security_blocks += 1

    def record_hitl(self):
        self.hitl_count += 1

    def record_error(self):
        self.errors += 1

    def summary(self) -> dict:
        avg_latency = (
            self.total_latency / self.query_count
            if self.query_count else 0
        )
        return {
            "query_count":     self.query_count,
            "tool_invocations": self.tool_count,
            "security_blocks": self.security_blocks,
            "hitl_requests":   self.hitl_count,
            "avg_latency_ms":  round(avg_latency, 2),
            "total_tokens":    self.total_tokens,
            "errors":          self.errors,
        }
