"""
agents/multi_agent.py
5-Agent System (multi-tenant aware):
  1. OrchestratorAgent  — coordinates all agents
  2. SecurityAgent      — resolves RBAC db_types for the user's role + tenant
  3. RetrievalAgent     — MongoDB Atlas Vector Search + Graph RAG + web scraping
  4. ValidationAgent    — cross-checks data accuracy, triggers HITL
  5. ToolAgent          — detects + queues plugin actions
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List
from core.rag import SelfCorrectingRAG, RetrievalResult, ConfidenceLevel
from security.rbac import RBACController, Role

logger = logging.getLogger(__name__)


# ── Shared task context ───────────────────────────────────────────────────

@dataclass
class AgentContext:
    user_id:          str
    session_id:       str
    user_role:        Role
    query:            str
    tenant_id:        str                    = ""     # ← NEW: company workspace scope
    allowed_db_types: List[str]              = field(default_factory=list)
    retrieval:        Optional[RetrievalResult] = None
    tool_actions:     List[dict]             = field(default_factory=list)
    validated:        bool                   = False
    blocked:          bool                   = False
    block_reason:     str                    = ""
    hitl_required:    bool                   = False
    hitl_reason:      str                    = ""
    final_answer:     str                    = ""


# ── Agent base ────────────────────────────────────────────────────────────

class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def run(self, ctx: AgentContext) -> AgentContext:
        raise NotImplementedError


# ── 1. Security Agent ─────────────────────────────────────────────────────

class SecurityAgent(BaseAgent):
    """
    Resolves which MongoDB Atlas db_types the user can access via RBAC.
    Sets ctx.allowed_db_types = ['public'] or ['public', 'private'].
    """

    def __init__(self, rbac: RBACController):
        super().__init__("SecurityAgent")
        self.rbac = rbac

    def run(self, ctx: AgentContext) -> AgentContext:
        logger.info(
            f"[{self.name}] RBAC check | user={ctx.user_id} "
            f"| role={ctx.user_role.value} | tenant={ctx.tenant_id}"
        )
        ctx.allowed_db_types = self.rbac.get_allowed_db_types(ctx.user_role)
        logger.info(f"[{self.name}] Allowed db_types: {ctx.allowed_db_types}")
        return ctx


# ── 2. Retrieval Agent ────────────────────────────────────────────────────

class RetrievalAgent(BaseAgent):
    """
    Searches MongoDB Atlas (tenant + RBAC filtered) and Knowledge Graph.
    Falls back to web scraping on low confidence.
    """

    def __init__(self, rag: SelfCorrectingRAG, web_scraper=None):
        super().__init__("RetrievalAgent")
        self.rag         = rag
        self.web_scraper = web_scraper

    def run(self, ctx: AgentContext) -> AgentContext:
        if ctx.blocked:
            return ctx

        logger.info(
            f"[{self.name}] Retrieving | tenant={ctx.tenant_id} "
            f"| db_types={ctx.allowed_db_types} | query={ctx.query[:60]}"
        )

        # MongoDB Atlas Vector Search + Graph RAG (tenant-scoped, RBAC filtered)
        ctx.retrieval = self.rag.retrieve(
            query            = ctx.query,
            tenant_id        = ctx.tenant_id,
            allowed_db_types = ctx.allowed_db_types,
            top_k            = 10,
        )

        # Web scraping fallback for low-confidence results
        if ctx.retrieval.confidence == ConfidenceLevel.LOW and self.web_scraper:
            logger.info(f"[{self.name}] Low confidence — attempting web scrape")
            scraped = self.web_scraper.scrape(ctx.query)
            if scraped:
                from core.rag import Chunk
                for s in scraped:
                    ctx.retrieval.chunks.append(Chunk(
                        content   = s.content,
                        # Mark distinctly so the LLM system prompt catches it
                        source    = f"[WEB] {s.source}", 
                        timestamp = s.timestamp,
                        score     = s.score,
                    ))
                ctx.retrieval.sources.append("web_scraping")

        return ctx


# ── 3. Validation Agent ───────────────────────────────────────────────────

class ValidationAgent(BaseAgent):
    """Cross-checks retrieval results. Only flags HITL for sensitive + low-confidence queries."""

    # Keywords that indicate the query is genuinely sensitive
    SENSITIVE_KEYWORDS = [
        "salary", "approve", "delete", "fire", "terminate",
        "financial", "legal", "compliance", "lawsuit", "contract",
        "confidential", "private", "secret", "payroll", "budget",
        "dismiss", "layoff", "redundancy", "audit",
    ]

    def __init__(self):
        super().__init__("ValidationAgent")

    def _is_sensitive(self, query: str) -> bool:
        q = query.lower()
        return any(kw in q for kw in self.SENSITIVE_KEYWORDS)

    def run(self, ctx: AgentContext) -> AgentContext:
        if ctx.blocked or not ctx.retrieval:
            return ctx

        logger.info(
            f"[{self.name}] Validating | "
            f"confidence={ctx.retrieval.confidence.value}"
        )

        if ctx.retrieval.conflicts:
            logger.warning(
                f"[{self.name}] Conflicts: {ctx.retrieval.conflicts}"
            )

        # Trigger HITL/Warning when confidence is not HIGH
        if ctx.retrieval.confidence != ConfidenceLevel.HIGH:
            ctx.hitl_required = True
            
            reason_msg = "Non-high confidence retrieval."
            if self._is_sensitive(ctx.query):
                reason_msg = "Sensitive query with non-high confidence retrieval."
                
            ctx.hitl_reason = (
                f"{reason_msg} "
                f"Conflicts: {ctx.retrieval.conflicts or 'None'}"
            )
            logger.info(f"[{self.name}] HITL triggered: {reason_msg}")

        ctx.validated = True
        return ctx


# ── 4. Tool Agent ─────────────────────────────────────────────────────────

class ToolAgent(BaseAgent):
    """
    Detects tool intent from query.
    Maps to registered plugins and queues actions.
    """

    # Trigger keyword → (plugin_name, action)
    TOOL_MAP = {
        # Google Suite
        "save":           ("google_drive",    "save_file"),
        "upload":         ("google_drive",    "upload_document"),
        "share file":     ("google_drive",    "share_folder"),
        "create doc":     ("google_docs",     "create_document"),
        "write document": ("google_docs",     "create_document"),
        "draft doc":      ("google_docs",     "create_document"),
        "edit document":  ("google_docs",     "edit_document"),
        "push data":      ("google_sheets",   "push_data"),
        "log to sheet":   ("google_sheets",   "update_row"),
        "update row":     ("google_sheets",   "update_row"),
        "schedule":       ("google_calendar", "create_event"),
        "create event":   ("google_calendar", "create_event"),
        "remind me":      ("google_calendar", "set_reminder"),
        "send email":     ("gmail",           "send_email"),
        "draft mail":     ("gmail",           "draft_email"),
        "email to":       ("gmail",           "send_email"),
        "meet link":      ("google_meet",     "create_link"),
        "video call":     ("google_meet",     "schedule_call"),
    }

    # Plugins where user must confirm before execution
    CONFIRM_REQUIRED = {"gmail", "google_docs"}

    # Keywords that always trigger HITL
    HITL_REQUIRED_KEYWORDS = [
        "salary", "approve", "all staff", "delete", "financial",
        "legal", "compliance", "bulk", "all employees",
    ]

    def __init__(self):
        super().__init__("ToolAgent")

    def run(self, ctx: AgentContext) -> AgentContext:
        if ctx.blocked:
            return ctx

        query_lower = ctx.query.lower()
        detected    = []

        for trigger, (plugin, action) in self.TOOL_MAP.items():
            if trigger in query_lower:
                requires_confirm = plugin in self.CONFIRM_REQUIRED
                requires_hitl    = any(
                    kw in query_lower for kw in self.HITL_REQUIRED_KEYWORDS
                )

                detected.append({
                    "plugin":           plugin,
                    "action":           action,
                    "requires_confirm": requires_confirm,
                    "requires_hitl":    requires_hitl,
                    "status":           "pending",
                })

                if requires_hitl:
                    ctx.hitl_required = True
                    ctx.hitl_reason   = (
                        f"High-risk action detected: {plugin}.{action}"
                    )
                    logger.info(
                        f"[{self.name}] HITL required: {plugin}.{action}"
                    )

                logger.info(f"[{self.name}] Tool detected: {plugin}.{action}")

        ctx.tool_actions = detected
        return ctx


# ── 5. Orchestrator Agent ─────────────────────────────────────────────────

class OrchestratorAgent(BaseAgent):
    """Coordinates all agents and assembles the final context string."""

    def __init__(self, security: SecurityAgent, retrieval: RetrievalAgent,
                 validation: ValidationAgent, tool: ToolAgent):
        super().__init__("OrchestratorAgent")
        self.security   = security
        self.retrieval  = retrieval
        self.validation = validation
        self.tool       = tool

    def run(self, ctx: AgentContext) -> AgentContext:
        logger.info(
            f"[{self.name}] Pipeline start | "
            f"user={ctx.user_id} | tenant={ctx.tenant_id}"
        )

        ctx = self.security.run(ctx)
        if ctx.blocked:
            return ctx

        ctx = self.retrieval.run(ctx)
        ctx = self.validation.run(ctx)
        ctx = self.tool.run(ctx)

        logger.info(
            f"[{self.name}] Pipeline complete | "
            f"hitl={ctx.hitl_required} | tools={len(ctx.tool_actions)}"
        )
        return ctx

    def build_context_string(self, ctx: AgentContext) -> str:
        """Build the retrieved context string to inject into the LLM prompt."""
        if not ctx.retrieval or not ctx.retrieval.chunks:
            return "No relevant internal data found."

        # Sort by relevance score (highest first) before taking top N
        top_chunks = sorted(
            ctx.retrieval.chunks, key=lambda c: c.score, reverse=True
        )[:8]   # top 8 most relevant chunks

        lines = []
        for i, chunk in enumerate(top_chunks, 1):
            db_label = "[CONFIDENTIAL]" if chunk.category == "private" else ""
            lines.append(
                f"[{i}] Source: {chunk.source} {db_label}"
                f" | Score: {chunk.score:.2f}\n{chunk.content}\n"
            )

        if ctx.retrieval.conflicts:
            lines.append(
                f"\n[⚠ DATA CONFLICT: Sources disagree — "
                f"{', '.join(ctx.retrieval.conflicts)}]"
            )

        return "\n".join(lines)
