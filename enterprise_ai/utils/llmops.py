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
from datetime import datetime, timedelta
from typing import Optional, Any
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)




# ── Log entry ─────────────────────────────────────────────────────────────

@dataclass
class InteractionLog:
    interaction_id:  str
    user_id:         str
    tenant_id:       str
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

    def summary(self, days: int = 7, tenant_id: Optional[str] = None) -> dict:
        """Aggregate dashboard metrics from persisted interaction logs."""
        days = max(1, min(days, 30))
        now = datetime.utcnow()
        window_start = now - timedelta(days=days)
        previous_start = window_start - timedelta(days=days)

        current_rows: list[dict[str, Any]] = []
        previous_count = 0

        if not self.log_file.exists():
            return self._empty_summary(days)

        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if tenant_id and str(row.get("tenant_id", "")).strip() != tenant_id:
                        continue

                    ts_raw = str(row.get("timestamp", "")).strip()
                    if not ts_raw:
                        continue

                    try:
                        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00").replace("+00:00", ""))
                    except ValueError:
                        continue

                    if ts >= window_start:
                        current_rows.append(row)
                    elif previous_start <= ts < window_start:
                        previous_count += 1
        except OSError:
            return self._empty_summary(days)

        if not current_rows:
            empty = self._empty_summary(days)
            empty["previous_query_count"] = previous_count
            return empty

        total_latency = 0.0
        total_tokens = 0
        tool_invocations = 0
        security_blocks = 0
        hitl_requests = 0
        errors = 0
        confidence_counter: Counter[str] = Counter()

        for row in current_rows:
            total_latency += float(row.get("latency_ms", 0.0) or 0.0)
            total_tokens += int(row.get("token_count", 0) or 0)
            tool_invocations += len(row.get("tool_actions", []) or [])
            security_events = row.get("security_events", []) or []
            security_blocks += sum(1 for e in security_events if "BLOCKED" in str(e).upper())
            if bool(row.get("hitl_triggered", False)):
                hitl_requests += 1
            if row.get("error"):
                errors += 1

            conf = str(row.get("confidence", "")).strip().lower()
            if conf in ("high", "medium", "low"):
                confidence_counter[conf] += 1
            elif conf in ("n/a", "na", ""):
                confidence_counter["low"] += 1
            else:
                confidence_counter["low"] += 1

        series_labels, series_values = self._build_query_series(current_rows, days)

        return {
            "period_days": days,
            "query_count": len(current_rows),
            "previous_query_count": previous_count,
            "tool_invocations": tool_invocations,
            "security_blocks": security_blocks,
            "hitl_requests": hitl_requests,
            "avg_latency_ms": round(total_latency / len(current_rows), 2),
            "total_tokens": total_tokens,
            "errors": errors,
            "confidence_breakdown": {
                "high": int(confidence_counter.get("high", 0)),
                "medium": int(confidence_counter.get("medium", 0)),
                "low": int(confidence_counter.get("low", 0)),
            },
            "query_timeseries": {
                "labels": series_labels,
                "values": series_values,
            },
        }

    def _empty_summary(self, days: int) -> dict:
        labels = self._default_labels(days)
        return {
            "period_days": days,
            "query_count": 0,
            "previous_query_count": 0,
            "tool_invocations": 0,
            "security_blocks": 0,
            "hitl_requests": 0,
            "avg_latency_ms": 0.0,
            "total_tokens": 0,
            "errors": 0,
            "confidence_breakdown": {"high": 0, "medium": 0, "low": 0},
            "query_timeseries": {
                "labels": labels,
                "values": [0 for _ in labels],
            },
        }

    def _default_labels(self, days: int) -> list[str]:
        today = datetime.utcnow().date()
        labels = []
        for offset in range(days - 1, -1, -1):
            day = today - timedelta(days=offset)
            labels.append(day.strftime("%a") if days <= 7 else day.strftime("%d %b"))
        return labels

    def _build_query_series(self, rows: list[dict[str, Any]], days: int) -> tuple[list[str], list[int]]:
        today = datetime.utcnow().date()
        daily_counts: dict[str, int] = {}

        for row in rows:
            ts_raw = str(row.get("timestamp", "")).strip()
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00").replace("+00:00", ""))
            except ValueError:
                continue
            key = ts.date().isoformat()
            daily_counts[key] = daily_counts.get(key, 0) + 1

        labels: list[str] = []
        values: list[int] = []
        for offset in range(days - 1, -1, -1):
            day = today - timedelta(days=offset)
            day_key = day.isoformat()
            labels.append(day.strftime("%a") if days <= 7 else day.strftime("%d %b"))
            values.append(daily_counts.get(day_key, 0))

        return labels, values




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
