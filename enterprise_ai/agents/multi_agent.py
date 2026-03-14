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
                        source    = s.source,
                        timestamp = s.timestamp,
                        score     = s.score,
                    ))
                ctx.retrieval.sources.append("web_scraping")

        return ctx


# ── 3. Validation Agent ───────────────────────────────────────────────────

class ValidationAgent(BaseAgent):
    """Cross-checks retrieval results. Flags HITL if confidence is LOW."""

    HITL_THRESHOLD = ConfidenceLevel.LOW

    def __init__(self):
        super().__init__("ValidationAgent")

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

        if ctx.retrieval.confidence == ConfidenceLevel.LOW:
            ctx.hitl_required = True
            ctx.hitl_reason   = (
                f"Low confidence retrieval (score below threshold). "
                f"Conflicts: {ctx.retrieval.conflicts or 'None'}"
            )
            logger.info(f"[{self.name}] HITL triggered: low confidence")

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

        lines = []
        for chunk in ctx.retrieval.chunks[:6]:   # Top 6 chunks
            lines.append(f"[Source: {chunk.source}]\n{chunk.content}\n")

        if ctx.retrieval.conflicts:
            lines.append(
                f"\n[NOTE: Conflicting data from: "
                f"{', '.join(ctx.retrieval.conflicts)}]"
            )

        return "\n".join(lines)
