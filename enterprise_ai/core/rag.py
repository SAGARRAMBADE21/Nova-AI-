"""
core/rag.py
Graph RAG   — NetworkX entity-relationship graph
Self-correcting RAG — relevance scoring + conflict detection + query reframing

Note: ChromaDB VectorStore has been replaced by TenantVectorStore (db/mongodb.py).
      Tenant-scoped + RBAC-filtered vector search is now handled by MongoDB Atlas.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

import networkx as nx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


# ── Data structures ───────────────────────────────────────────────────────

class ConfidenceLevel(Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"


@dataclass
class Chunk:
    content:   str
    source:    str
    timestamp: str
    score:     float = 0.0
    category:  str   = "general"


@dataclass
class RetrievalResult:
    chunks:         List[Chunk]
    confidence:     ConfidenceLevel
    conflicts:      List[str]
    reframed_query: Optional[str]
    sources:        List[str]


# ── Knowledge Graph (NetworkX) ────────────────────────────────────────────

class KnowledgeGraph:
    """Entity-relationship graph for Graph RAG cross-document reasoning."""

    def __init__(self):
        self.graph = nx.DiGraph()
        logger.info("[KnowledgeGraph] Initialised.")

    def add_entity(self, entity: str, entity_type: str, source: str):
        self.graph.add_node(entity, type=entity_type, source=source)

    def add_relationship(self, entity_a: str, entity_b: str,
                         relation: str, source: str):
        self.graph.add_edge(
            entity_a, entity_b, relation=relation, source=source
        )

    def query(self, query: str, top_k: int = 5) -> list[dict]:
        """Find entities and relationships relevant to the query."""
        results     = []
        query_lower = query.lower()

        for node in self.graph.nodes(data=True):
            if query_lower in node[0].lower():
                neighbors = list(self.graph.neighbors(node[0]))
                edges = [
                    {
                        "from":     node[0],
                        "to":       n,
                        "relation": self.graph[node[0]][n].get("relation", ""),
                        "source":   self.graph[node[0]][n].get("source", ""),
                    }
                    for n in neighbors
                ]
                results.append({
                    "entity": node[0],
                    "type":   node[1].get("type"),
                    "edges":  edges,
                })
                if len(results) >= top_k:
                    break

        return results

    def update_from_document(self, content: str, source: str):
        """
        Naïve entity extraction — capitalised word sequences.
        In production replace with spaCy NER or OpenAI function calling.
        """
        import re
        candidates = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', content)
        for entity in set(candidates):
            self.add_entity(entity, "unknown", source)
        logger.info(f"[KnowledgeGraph] Updated from source: {source}")


# ── Self-Correcting RAG ───────────────────────────────────────────────────

class SelfCorrectingRAG:
    """
    Retrieves from MongoDB Atlas TenantVectorStore (tenant-scoped, RBAC-filtered).
    Also queries NetworkX KnowledgeGraph for entity-relationship context.
    Assigns confidence score — LOW confidence triggers HITL.
    """

    RELEVANCE_THRESHOLD  = 0.5
    MAX_REFRAME_ATTEMPTS = 3

    def __init__(self, public_store, private_store,
                 knowledge_graph: KnowledgeGraph):
        """
        public_store  — TenantVectorStore on nova_ai database          (all roles)
        private_store — TenantVectorStore on nova_ai_confidential db   (manager+ only)
        """
        self.public_store    = public_store
        self.private_store   = private_store
        self.knowledge_graph = knowledge_graph

    def retrieve(self, query: str,
                 tenant_id: str,
                 allowed_db_types: List[str],
                 top_k: int = 5,
                 attempt: int = 0) -> RetrievalResult:
        """
        Retrieve documents across the correct physical databases.

        Employees   → only public_store  (nova_ai) is queried
        Managers+   → public_store + private_store (nova_ai_confidential) queried

        The confidential database is NEVER touched for employee-role queries.
        """
        logger.info(
            f"[SelfCorrectingRAG] Attempt {attempt + 1} | "
            f"tenant={tenant_id} | db_types={allowed_db_types} | "
            f"query={query[:60]}"
        )

        raw: list[dict] = []

        # 1a. Always search public database (nova_ai)
        public_results = self.public_store.search(
            tenant_id        = tenant_id,
            query            = query,
            allowed_db_types = ["public"],
            top_k            = top_k,
        )
        raw.extend(public_results)
        logger.info(
            f"[SelfCorrectingRAG] Public DB hits: {len(public_results)}"
        )

        # 1b. Search confidential database ONLY if role allows (manager / admin)
        if "private" in allowed_db_types:
            private_results = self.private_store.search(
                tenant_id        = tenant_id,
                query            = query,
                allowed_db_types = ["private"],
                top_k            = top_k,
            )
            raw.extend(private_results)
            logger.info(
                f"[SelfCorrectingRAG] Confidential DB hits: {len(private_results)}"
            )
        else:
            logger.info(
                "[SelfCorrectingRAG] Confidential DB SKIPPED — role not permitted."
            )

        chunks: List[Chunk] = [
            Chunk(
                content   = r["content"],
                source    = r.get("source",    "unknown"),
                timestamp = r.get("timestamp", ""),
                score     = r.get("score",     0.0),
                category  = r.get("category",  "general"),
            )
            for r in raw
        ]

        # 2. Graph RAG
        graph_results = self.knowledge_graph.query(query)
        for gr in graph_results:
            for edge in gr.get("edges", []):
                chunks.append(Chunk(
                    content   = f"{edge['from']} {edge['relation']} {edge['to']}",
                    source    = edge.get("source", "knowledge_graph"),
                    timestamp = "",
                    score     = 0.7,
                ))

        # 3. Relevance filter
        relevant = [c for c in chunks if c.score >= self.RELEVANCE_THRESHOLD]

        # 4. Conflict detection
        conflicts = self._detect_conflicts(relevant)

        # 5. Confidence scoring
        confidence = self._score_confidence(relevant, conflicts)

        # 6. Query reframing if low quality
        reframed = None
        if confidence == ConfidenceLevel.LOW and attempt < self.MAX_REFRAME_ATTEMPTS:
            reframed = self._reframe_query(query)
            if reframed and reframed != query:
                logger.info(f"[SelfCorrectingRAG] Reframing query → {reframed}")
                return self.retrieve(
                    reframed, tenant_id, allowed_db_types,
                    top_k, attempt + 1
                )
            reframed = None

        sources = list({c.source for c in relevant})
        return RetrievalResult(
            chunks         = relevant,
            confidence     = confidence,
            conflicts      = conflicts,
            reframed_query = reframed,
            sources        = sources,
        )

    def _detect_conflicts(self, chunks: List[Chunk]) -> List[str]:
        conflicts = []
        seen: dict[str, str] = {}
        for chunk in chunks:
            key = chunk.source.split("/")[0]
            if key in seen and seen[key] != chunk.content[:100]:
                conflicts.append(f"Conflicting data from source: {chunk.source}")
            seen[key] = chunk.content[:100]
        return conflicts

    def _score_confidence(self, chunks: List[Chunk],
                          conflicts: List[str]) -> ConfidenceLevel:
        if not chunks:
            return ConfidenceLevel.LOW
        avg_score = sum(c.score for c in chunks) / len(chunks)
        if conflicts:
            avg_score *= 0.8
        if avg_score >= 0.75:
            return ConfidenceLevel.HIGH
        elif avg_score >= 0.50:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def _reframe_query(self, query: str) -> str:
        """Simplify query for better retrieval match."""
        stop_words = {"the", "a", "an", "is", "are", "was", "were",
                      "what", "how", "who"}
        words    = [w for w in query.split() if w.lower() not in stop_words]
        reframed = " ".join(words[:8])
        return reframed if reframed and len(reframed) >= 3 else query
