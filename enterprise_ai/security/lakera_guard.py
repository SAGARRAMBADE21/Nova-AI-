"""
security/lakera_guard.py
Lakera Guard — 3-checkpoint security layer
Checkpoint 1: Input Scan
Checkpoint 2: Document Scan
Checkpoint 3: Output Scan
"""

import os
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class ThreatType(Enum):
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK        = "jailbreak"
    PII              = "pii"
    UNKNOWN_LINKS    = "unknown_links"
    HALLUCINATION    = "hallucination"
    CLEAN            = "clean"


@dataclass
class ScanResult:
    flagged:    bool
    threat:     ThreatType
    confidence: float
    message:    str


class LakeraGuard:
    """
    Wraps all 3 Lakera Guard checkpoints.
    Called automatically on every request — never exposed to the user.
    """

    API_URL = "https://api.lakera.ai/v2/guard"

    def __init__(self):
        self.api_key    = os.getenv("LAKERA_API_KEY")
        self.project_id = os.getenv("LAKERA_PROJECT_ID")
        if not self.api_key or self.api_key == "your_lakera_api_key":
            logger.warning("[LakeraGuard] LAKERA_API_KEY not set. Running in pass-through mode.")
            self.api_key = None

    # ── Internal API call ─────────────────────────────────────────────────
    def _scan(self, messages: list, user_id: str, session_id: str) -> dict:
        if not self.api_key:
            # Pass-through mode — no Lakera key configured
            return {"results": [{"flagged": False, "categories": {}, "category_scores": {}}]}
        try:
            response = requests.post(
                self.API_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "project_id": self.project_id,
                    "messages":   messages,
                    "payload":    True,
                    "breakdown":  True,
                    "metadata": {
                        "user_id":    user_id,
                        "session_id": session_id,
                    },
                },
                timeout=5,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"[LakeraGuard] API error: {e}")
            # Fail closed — block on API error
            return {"results": [{"flagged": True, "categories": {"prompt_injection": True},
                                 "category_scores": {}}]}

    def _parse(self, raw: dict) -> ScanResult:
        result = raw.get("results", [{}])[0]
        flagged    = result.get("flagged", False)
        categories = result.get("categories", {})
        scores     = result.get("category_scores", {})

        if not flagged:
            return ScanResult(False, ThreatType.CLEAN, 0.0, "Clean")

        # Determine dominant threat
        if categories.get("prompt_injection"):
            threat = ThreatType.PROMPT_INJECTION
            msg    = "Prompt injection attack detected and blocked."
        elif categories.get("jailbreak"):
            threat = ThreatType.JAILBREAK
            msg    = "Jailbreak attempt detected and blocked."
        elif categories.get("pii"):
            threat = ThreatType.PII
            msg    = "PII detected. Please remove personal information."
        elif categories.get("unknown_links"):
            threat = ThreatType.UNKNOWN_LINKS
            msg    = "Unknown or malicious links detected."
        else:
            threat = ThreatType.PROMPT_INJECTION
            msg    = "Unsafe content detected."

        confidence = max(scores.values(), default=1.0)
        return ScanResult(True, threat, confidence, msg)

    # ── CHECKPOINT 1: Input Scan ─────────────────────────────────────────
    def scan_input(self, user_prompt: str, user_id: str, session_id: str) -> ScanResult:
        """Scan user prompt before it reaches the LLM."""
        logger.info(f"[LakeraGuard] Checkpoint 1: Input scan | user={user_id}")
        messages = [{"role": "user", "content": user_prompt}]
        raw    = self._scan(messages, user_id, session_id)
        result = self._parse(raw)
        if result.flagged:
            logger.warning(f"[LakeraGuard] INPUT BLOCKED | threat={result.threat.value} | user={user_id}")
        return result

    # ── CHECKPOINT 2: Document Scan ──────────────────────────────────────
    def scan_document(self, content: str, source: str, user_id: str, session_id: str) -> ScanResult:
        """Scan retrieved RAG chunk or uploaded document before injecting into LLM."""
        logger.info(f"[LakeraGuard] Checkpoint 2: Document scan | source={source}")
        messages = [{"role": "user", "content": content}]
        raw    = self._scan(messages, user_id, session_id)
        result = self._parse(raw)
        if result.flagged:
            logger.warning(f"[LakeraGuard] DOCUMENT BLOCKED | source={source} | threat={result.threat.value}")
        return result

    # ── CHECKPOINT 3: Output Scan ────────────────────────────────────────
    def scan_output(self, prompt: str, response: str, user_id: str, session_id: str) -> ScanResult:
        """Scan LLM response before delivering to user."""
        logger.info(f"[LakeraGuard] Checkpoint 3: Output scan | user={user_id}")
        messages = [
            {"role": "user",      "content": prompt},
            {"role": "assistant", "content": response},
        ]
        raw    = self._scan(messages, user_id, session_id)
        result = self._parse(raw)
        if result.flagged:
            logger.warning(f"[LakeraGuard] OUTPUT BLOCKED | threat={result.threat.value} | user={user_id}")
        return result

    # ── Safe fallback message ────────────────────────────────────────────
    @staticmethod
    def blocked_message(result: ScanResult) -> str:
        return (
            f"Your request could not be processed. "
            f"Reason: {result.message} "
            f"Please contact your administrator if you believe this is an error."
        )
