"""
core/hitl.py
Human-in-the-Loop (HITL)
Pauses high-risk tasks and routes to human reviewer.
3 escalation levels: Team Lead → Manager → Admin
"""

import os
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class HITLDecision(Enum):
    APPROVED = "approved"
    MODIFIED = "modified"
    REJECTED = "rejected"
    PENDING  = "pending"
    ESCALATED = "escalated"


class EscalationLevel(Enum):
    LEVEL_1 = "team_lead"
    LEVEL_2 = "department_manager"
    LEVEL_3 = "system_administrator"


@dataclass
class HITLRequest:
    request_id:        str
    user_id:           str
    session_id:        str
    query:             str
    reason:            str
    proposed_actions:  list[dict]
    confidence:        str
    risk_level:        str
    escalation_level:  EscalationLevel
    created_at:        datetime        = field(default_factory=datetime.utcnow)
    sla_deadline:      Optional[datetime] = None
    decision:          HITLDecision    = HITLDecision.PENDING
    reviewer_id:       Optional[str]   = None
    reviewer_notes:    str             = ""
    modified_actions:  list[dict]      = field(default_factory=list)

    def is_expired(self) -> bool:
        if not self.sla_deadline:
            return False
        return datetime.utcnow() > self.sla_deadline


class HITLController:
    """
    Manages HITL workflow.
    In production: integrate with email/Slack notifications to reviewers.
    """

    SLA_MINUTES = int(os.getenv("HITL_SLA_MINUTES", "30"))

    def __init__(self):
        # In production: replace with database
        self._pending: dict[str, HITLRequest] = {}
        logger.info("[HITL] Controller initialised.")

    def create_request(self, user_id: str, session_id: str,
                       query: str, reason: str,
                       proposed_actions: list[dict],
                       confidence: str,
                       risk_level: str = "high") -> HITLRequest:

        level    = self._determine_level(reason, risk_level)
        deadline = datetime.utcnow() + timedelta(minutes=self.SLA_MINUTES)

        request = HITLRequest(
            request_id       = str(uuid.uuid4()),
            user_id          = user_id,
            session_id       = session_id,
            query            = query,
            reason           = reason,
            proposed_actions = proposed_actions,
            confidence       = confidence,
            risk_level       = risk_level,
            escalation_level = level,
            sla_deadline     = deadline,
        )

        self._pending[request.request_id] = request
        self._notify_reviewer(request)

        logger.info(f"[HITL] Request created | id={request.request_id} | level={level.value}")
        return request

    def submit_decision(self, request_id: str, reviewer_id: str,
                        decision: HITLDecision,
                        notes: str = "",
                        modified_actions: Optional[list[dict]] = None) -> HITLRequest:

        request = self._pending.get(request_id)
        if not request:
            raise ValueError(f"HITL request not found: {request_id}")

        request.decision        = decision
        request.reviewer_id     = reviewer_id
        request.reviewer_notes  = notes
        request.modified_actions = modified_actions or []

        logger.info(f"[HITL] Decision submitted | id={request_id} | decision={decision.value} | reviewer={reviewer_id}")
        return request

    def check_and_escalate(self, request_id: str) -> HITLRequest:
        """Escalate if SLA has expired."""
        request = self._pending.get(request_id)
        if not request:
            raise ValueError(f"HITL request not found: {request_id}")

        if request.is_expired() and request.decision == HITLDecision.PENDING:
            next_level = self._escalate(request.escalation_level)
            if next_level:
                request.escalation_level = next_level
                request.sla_deadline     = datetime.utcnow() + timedelta(minutes=self.SLA_MINUTES)
                request.decision         = HITLDecision.ESCALATED
                self._notify_reviewer(request)
                logger.warning(f"[HITL] Escalated | id={request_id} | new_level={next_level.value}")

        return request

    def get_pending_message(self, request: HITLRequest) -> str:
        return (
            f"Your request is under review by your {request.escalation_level.value.replace('_', ' ').title()}. "
            f"You will be notified once a decision is made. "
            f"Request ID: {request.request_id} | SLA: {self.SLA_MINUTES} minutes."
        )

    def _determine_level(self, reason: str, risk_level: str) -> EscalationLevel:
        reason_lower = reason.lower()
        if any(kw in reason_lower for kw in ["security", "admin", "critical", "breach"]):
            return EscalationLevel.LEVEL_3
        if any(kw in reason_lower for kw in ["financial", "confidential", "legal", "hr"]):
            return EscalationLevel.LEVEL_2
        return EscalationLevel.LEVEL_1

    def _escalate(self, current: EscalationLevel) -> Optional[EscalationLevel]:
        escalation_path = {
            EscalationLevel.LEVEL_1: EscalationLevel.LEVEL_2,
            EscalationLevel.LEVEL_2: EscalationLevel.LEVEL_3,
            EscalationLevel.LEVEL_3: None,
        }
        return escalation_path.get(current)

    def _notify_reviewer(self, request: HITLRequest):
        """
        In production: send email/Slack notification to reviewer.
        Here we log the notification.
        """
        logger.info(
            f"[HITL] Notifying {request.escalation_level.value} | "
            f"request_id={request.request_id} | "
            f"user={request.user_id} | "
            f"reason={request.reason}"
        )
        # Example: send Slack DM to reviewer
        # slack_client.chat_postMessage(channel=reviewer_slack_id, text=...)
