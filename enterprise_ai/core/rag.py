"""
core/rag.py
Vector RAG  — ChromaDB semantic search
Graph RAG   — NetworkX entity-relationship graph
Self-correcting RAG — relevance scoring + conflict detection + query reframing
"""

import os
import logging
import hashlib
from dataclasses import dataclass, field
from typing import Optional
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
    content:    str
    source:     str
    timestamp:  str
    score:      float = 0.0
    category:   str   = "general"


@dataclass
class RetrievalResult:
    chunks:          list[Chunk]
    confidence:      ConfidenceLevel
    conflicts:       list[str]
    reframed_query:  Optional[str]
    sources:         list[str]


# ── Vector Store (ChromaDB) ───────────────────────────────────────────────

class VectorStore:
    """ChromaDB-backed semantic search over company documents."""

    def __init__(self):
        try:
            import chromadb
            persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
            self.client     = chromadb.PersistentClient(path=persist_dir)
            self.collection = self.client.get_or_create_collection(
                name="company_knowledge",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("[VectorStore] ChromaDB initialised.")
        except ImportError:
            logger.warning("[VectorStore] ChromaDB not installed. Using mock store.")
            self.client     = None
            self.collection = None

    def add_document(self, content: str, source: str,
                     timestamp: str, category: str = "general") -> str:
        doc_id = hashlib.md5(f"{source}{timestamp}".encode()).hexdigest()
        if self.collection:
            self.collection.add(
                documents=[content],
                ids=[doc_id],
                metadatas=[{"source": source, "timestamp": timestamp, "category": category}],
            )
        logger.info(f"[VectorStore] Document added | source={source}")
        return doc_id

    def search(self, query: str, top_k: int = 5,
               category_filter: Optional[str] = None) -> list[Chunk]:
        if not self.collection:
            return []
        where = {"category": category_filter} if category_filter else None
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where,
            )
            chunks = []
            for i, doc in enumerate(results["documents"][0]):
                meta  = results["metadatas"][0][i]
                score = 1 - results["distances"][0][i]  # cosine similarity
                chunks.append(Chunk(
                    content   = doc,
                    source    = meta.get("source", "unknown"),
                    timestamp = meta.get("timestamp", ""),
                    score     = score,
                    category  = meta.get("category", "general"),
                ))
            return chunks
        except Exception as e:
            logger.error(f"[VectorStore] Search error: {e}")
            return []


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
        self.graph.add_edge(entity_a, entity_b, relation=relation, source=source)

    def query(self, query: str, top_k: int = 5) -> list[dict]:
        """Find entities and relationships relevant to the query."""
        results = []
        query_lower = query.lower()

        for node in self.graph.nodes(data=True):
            if query_lower in node[0].lower():
                neighbors = list(self.graph.neighbors(node[0]))
                edges     = [
                    {
                        "from":     node[0],
                        "to":       n,
                        "relation": self.graph[node[0]][n].get("relation", ""),
                        "source":   self.graph[node[0]][n].get("source", ""),
                    }
                    for n in neighbors
                ]
                results.append({"entity": node[0], "type": node[1].get("type"), "edges": edges})
                if len(results) >= top_k:
                    break

        return results

    def update_from_document(self, content: str, source: str):
        """
        Naive entity extraction — in production replace with
        spaCy NER or OpenAI function calling for entity extraction.
        """
        import re
        # Extract capitalised words as candidate entities
        candidates = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', content)
        for entity in set(candidates):
            self.add_entity(entity, "unknown", source)
        logger.info(f"[KnowledgeGraph] Updated from source: {source}")


# ── Self-Correcting RAG ───────────────────────────────────────────────────

class SelfCorrectingRAG:
    """
    Evaluates, cross-checks, and self-corrects retrieval results.
    Assigns confidence score — low confidence triggers HITL.
    """

    RELEVANCE_THRESHOLD  = 0.5
    MAX_REFRAME_ATTEMPTS = 3

    def __init__(self, vector_store: VectorStore, knowledge_graph: KnowledgeGraph):
        self.vector_store    = vector_store
        self.knowledge_graph = knowledge_graph

    def retrieve(self, query: str, top_k: int = 5,
                 attempt: int = 0) -> RetrievalResult:
        logger.info(f"[SelfCorrectingRAG] Retrieval attempt {attempt + 1} | query={query[:60]}")

        # 1. Vector search
        chunks = self.vector_store.search(query, top_k=top_k)

        # 2. Graph RAG
        graph_results = self.knowledge_graph.query(query)
        for gr in graph_results:
            for edge in gr.get("edges", []):
                graph_chunk = Chunk(
                    content   = f"{edge['from']} {edge['relation']} {edge['to']}",
                    source    = edge.get("source", "knowledge_graph"),
                    timestamp = "",
                    score     = 0.7,
                )
                chunks.append(graph_chunk)

        # 3. Relevance filter
        relevant = [c for c in chunks if c.score >= self.RELEVANCE_THRESHOLD]

        # 4. Conflict detection
        conflicts = self._detect_conflicts(relevant)

        # 5. Confidence scoring
        confidence = self._score_confidence(relevant, conflicts)

        # 6. Query reframing if quality is low
        reframed = None
        if confidence == ConfidenceLevel.LOW and attempt < self.MAX_REFRAME_ATTEMPTS:
            reframed = self._reframe_query(query)
            # Only recurse if the reframing actually changed the query
            if reframed and reframed != query:
                logger.info(f"[SelfCorrectingRAG] Reframing query: {reframed}")
                return self.retrieve(reframed, top_k, attempt + 1)
            else:
                logger.info("[SelfCorrectingRAG] Reframe produced no change, stopping early.")
                reframed = None

        sources = list({c.source for c in relevant})
        return RetrievalResult(
            chunks         = relevant,
            confidence     = confidence,
            conflicts      = conflicts,
            reframed_query = reframed,
            sources        = sources,
        )

    def _detect_conflicts(self, chunks: list[Chunk]) -> list[str]:
        conflicts = []
        seen: dict[str, str] = {}
        for chunk in chunks:
            key = chunk.source.split("/")[0]  # Group by root source
            if key in seen and seen[key] != chunk.content[:100]:
                conflicts.append(f"Conflicting data from source: {chunk.source}")
            seen[key] = chunk.content[:100]
        return conflicts

    def _score_confidence(self, chunks: list[Chunk],
                          conflicts: list[str]) -> ConfidenceLevel:
        if not chunks:
            return ConfidenceLevel.LOW
        avg_score = sum(c.score for c in chunks) / len(chunks)
        if conflicts:
            avg_score *= 0.8  # Penalise for conflicts
        if avg_score >= 0.75:
            return ConfidenceLevel.HIGH
        elif avg_score >= 0.50:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def _reframe_query(self, query: str) -> str:
        """Simplify query for better retrieval. Returns original if no improvement possible."""
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "what", "how", "who"}
        words      = [w for w in query.split() if w.lower() not in stop_words]
        reframed   = " ".join(words[:8])
        # Return original query if reframing strips too much content
        return reframed if reframed and len(reframed) >= 3 else query
