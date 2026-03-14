"""
agents/multi_agent.py
5-Agent System:
  1. OrchestratorAgent  — coordinates all agents
  2. RetrievalAgent     — RAG + Graph RAG + web scraping
  3. ValidationAgent    — cross-checks data accuracy
  4. ToolAgent          — detects + invokes plugins
  5. SecurityAgent      — enforces RBAC + Lakera Guard
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Any
from core.rag import SelfCorrectingRAG, RetrievalResult, ConfidenceLevel
from security.rbac import RBACController, Role, DataCategory

logger = logging.getLogger(__name__)


# ── Shared task context ───────────────────────────────────────────────────

@dataclass
class AgentContext:
    user_id:       str
    session_id:    str
    user_role:     Role
    query:         str
    retrieval:     Optional[RetrievalResult] = None
    tool_actions:  list[dict]                = field(default_factory=list)
    validated:     bool                      = False
    blocked:       bool                      = False
    block_reason:  str                       = ""
    hitl_required: bool                      = False
    hitl_reason:   str                       = ""
    final_answer:  str                       = ""


# ── Agent base ────────────────────────────────────────────────────────────

class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def run(self, ctx: AgentContext) -> AgentContext:
        raise NotImplementedError


# ── 1. Security Agent ─────────────────────────────────────────────────────

class SecurityAgent(BaseAgent):
    """Enforces RBAC. Works alongside Lakera Guard checkpoints."""

    def __init__(self, rbac: RBACController):
        super().__init__("SecurityAgent")
        self.rbac = rbac

    def run(self, ctx: AgentContext) -> AgentContext:
        logger.info(f"[{self.name}] Checking access | user={ctx.user_id} | role={ctx.user_role.value}")
        category = self.rbac.classify_query(ctx.query)
        if not self.rbac.check_access(ctx.user_role, category):
            ctx.blocked     = True
            ctx.block_reason = self.rbac.get_denied_message(ctx.user_role, category)
            logger.warning(f"[{self.name}] Access blocked | user={ctx.user_id}")
        return ctx


# ── 2. Retrieval Agent ────────────────────────────────────────────────────

class RetrievalAgent(BaseAgent):
    """Searches vector store, knowledge graph, and web scraper."""

    def __init__(self, rag: SelfCorrectingRAG, web_scraper=None):
        super().__init__("RetrievalAgent")
        self.rag         = rag
        self.web_scraper = web_scraper

    def run(self, ctx: AgentContext) -> AgentContext:
        if ctx.blocked:
            return ctx
        logger.info(f"[{self.name}] Retrieving data | query={ctx.query[:60]}")
        ctx.retrieval = self.rag.retrieve(ctx.query)

        # Web scraping fallback
        if (ctx.retrieval.confidence == ConfidenceLevel.LOW
                and self.web_scraper):
            logger.info(f"[{self.name}] Low confidence — attempting web scrape")
            scraped = self.web_scraper.scrape(ctx.query)
            if scraped:
                from core.rag import Chunk
                ctx.retrieval.chunks.extend(scraped)
                ctx.retrieval.sources.append("web_scraping")

        return ctx


# ── 3. Validation Agent ───────────────────────────────────────────────────

class ValidationAgent(BaseAgent):
    """Cross-checks retrieval results. Flags HITL if confidence is low."""

    HITL_THRESHOLD = ConfidenceLevel.LOW

    def __init__(self):
        super().__init__("ValidationAgent")

    def run(self, ctx: AgentContext) -> AgentContext:
        if ctx.blocked or not ctx.retrieval:
            return ctx

        logger.info(f"[{self.name}] Validating | confidence={ctx.retrieval.confidence.value}")

        # Flag conflicts
        if ctx.retrieval.conflicts:
            logger.warning(f"[{self.name}] Conflicts detected: {ctx.retrieval.conflicts}")

        # Trigger HITL for low confidence
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

    # Trigger → (plugin_name, action)
    TOOL_MAP = {
        # Google Suite
        "save":              ("google_drive",    "save_file"),
        "upload":            ("google_drive",    "upload_document"),
        "share file":        ("google_drive",    "share_folder"),
        "create doc":        ("google_docs",     "create_document"),
        "write document":    ("google_docs",     "create_document"),
        "draft doc":         ("google_docs",     "create_document"),
        "edit document":     ("google_docs",     "edit_document"),
        "push data":         ("google_sheets",   "push_data"),
        "log to sheet":      ("google_sheets",   "update_row"),
        "update row":        ("google_sheets",   "update_row"),
        "schedule":          ("google_calendar", "create_event"),
        "create event":      ("google_calendar", "create_event"),
        "remind me":         ("google_calendar", "set_reminder"),
        "send email":        ("gmail",           "send_email"),
        "draft mail":        ("gmail",           "draft_email"),
        "email to":          ("gmail",           "send_email"),
        "meet link":         ("google_meet",     "create_link"),
        "video call":        ("google_meet",     "schedule_call"),
        # Dashboard
        "dashboard":         ("grafana",         "update_dashboard"),
        "push metrics":      ("grafana",         "push_metrics"),
        "update panel":      ("grafana",         "create_panel"),
        "kpi":               ("grafana",         "update_dashboard"),
        "analytics":         ("grafana",         "update_dashboard"),
    }

    # Actions that require user confirmation before execution
    CONFIRM_REQUIRED = {
        "gmail", "grafana", "google_docs"
    }

    # Actions that require HITL
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
                requires_hitl    = any(kw in query_lower for kw in self.HITL_REQUIRED_KEYWORDS)

                detected.append({
                    "plugin":           plugin,
                    "action":           action,
                    "requires_confirm": requires_confirm,
                    "requires_hitl":    requires_hitl,
                    "status":           "pending",
                })

                if requires_hitl:
                    ctx.hitl_required = True
                    ctx.hitl_reason   = f"High-risk action detected: {plugin}.{action}"
                    logger.info(f"[{self.name}] HITL required: {plugin}.{action}")

                logger.info(f"[{self.name}] Tool detected: {plugin}.{action}")

        ctx.tool_actions = detected
        return ctx


# ── 5. Orchestrator Agent ─────────────────────────────────────────────────

class OrchestratorAgent(BaseAgent):
    """
    Coordinates all agents.
    Assembles the final unified response.
    """

    def __init__(self, security: SecurityAgent, retrieval: RetrievalAgent,
                 validation: ValidationAgent, tool: ToolAgent):
        super().__init__("OrchestratorAgent")
        self.security   = security
        self.retrieval  = retrieval
        self.validation = validation
        self.tool       = tool

    def run(self, ctx: AgentContext) -> AgentContext:
        logger.info(f"[{self.name}] Starting pipeline | user={ctx.user_id}")

        # Run agents in order
        ctx = self.security.run(ctx)
        if ctx.blocked:
            return ctx

        ctx = self.retrieval.run(ctx)
        ctx = self.validation.run(ctx)
        ctx = self.tool.run(ctx)

        logger.info(f"[{self.name}] Pipeline complete | hitl={ctx.hitl_required} | tools={len(ctx.tool_actions)}")
        return ctx

    def build_context_string(self, ctx: AgentContext) -> str:
        """Build the context string to inject into the LLM prompt."""
        if not ctx.retrieval or not ctx.retrieval.chunks:
            return "No relevant internal data found."

        lines = []
        for chunk in ctx.retrieval.chunks[:6]:  # Top 6 chunks
            lines.append(f"[Source: {chunk.source}]\n{chunk.content}\n")

        if ctx.retrieval.conflicts:
            lines.append(f"\n[NOTE: Conflicting data detected from: {', '.join(ctx.retrieval.conflicts)}]")

        return "\n".join(lines)
