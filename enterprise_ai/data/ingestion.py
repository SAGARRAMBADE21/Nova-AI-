"""
data/ingestion.py
Real-Time Admin Data Ingestion (24/7) — Multi-tenant aware.
Supports: PDF, DOCX, XLSX, CSV, TXT, JSON, XML, URLs
Pipeline: Upload → Lakera Scan → Parse → Chunk → Embed (MongoDB Atlas) → Graph Update
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class DataIngestionPipeline:

    SUPPORTED_FORMATS = {
        ".pdf":  "_parse_pdf",
        ".docx": "_parse_docx",
        ".xlsx": "_parse_xlsx",
        ".csv":  "_parse_csv",
        ".txt":  "_parse_text",
        ".json": "_parse_json",
        ".xml":  "_parse_xml",
        ".md":   "_parse_text",
    }

    def __init__(self, public_store, private_store,
                 knowledge_graph, lakera_guard=None):
        """
        public_store  → nova_ai database           (db_type='public')
        private_store → nova_ai_confidential db    (db_type='private')
        """
        self.public_store    = public_store
        self.private_store   = private_store
        self.knowledge_graph = knowledge_graph
        self.lakera          = lakera_guard

    # ── Main entry point ─────────────────────────────────────────────────

    def ingest(self, file_path: str,
               tenant_id: str,
               category: str    = "general",
               uploaded_by: str = "admin",
               db_type: str     = "public",
               original_filename: str = "") -> dict:
        """
        Full ingestion pipeline for a single file.

        tenant_id         — company workspace scope (required)
        db_type='public'  → visible to all roles
        db_type='private' → visible to manager, team_lead, admin only
        original_filename — display name to use as source (overrides temp path)
        Returns ingestion report dict.
        """
        path      = Path(file_path)
        # Use original filename if provided (avoids showing tmp paths like tmpewtij2bc.pdf)
        source_name = original_filename or path.name
        timestamp = datetime.utcnow().isoformat()


        logger.info(
            f"[Ingestion] Starting | tenant={tenant_id} | "
            f"file={path.name} | db_type={db_type} | category={category}"
        )

        # 1. Parse content
        content = self._parse(path)
        if not content:
            return {
                "status": "failed",
                "reason": "Could not parse file",
                "file":   path.name,
            }

        # 2. Lakera Guard scan
        if self.lakera:
            result = self.lakera.scan_document(
                content[:2000], source_name, "admin", "ingestion"
            )
            if result.flagged:
                logger.warning(
                    f"[Ingestion] Lakera blocked | file={source_name} "
                    f"| threat={result.threat.value}"
                )
                return {
                    "status": "blocked",
                    "reason": result.message,
                    "file":   source_name,
                }

        # 3. Chunk
        chunks = self._chunk(content)

        # 4. Route to correct physical database based on db_type
        store = self.public_store if db_type == "public" else self.private_store
        db_label = "nova_ai" if db_type == "public" else "nova_ai_confidential"
        logger.info(
            f"[Ingestion] Routing to {db_label} | db_type={db_type}"
        )
        for chunk in chunks:
            store.add_document(
                tenant_id = tenant_id,
                content   = chunk,
                source    = source_name,
                timestamp = timestamp,
                category  = category,
                db_type   = db_type,
            )

        # 5. Update knowledge graph
        self.knowledge_graph.update_from_document(content, source_name)

        report = {
            "status":      "success",
            "file":        source_name,
            "chunks":      len(chunks),
            "category":    category,
            "db_type":     db_type,
            "tenant_id":   tenant_id,
            "uploaded_by": uploaded_by,
            "timestamp":   timestamp,
        }
        logger.info(f"[Ingestion] Complete | {report}")
        return report

    def ingest_directory(self, directory: str,
                         tenant_id: str,
                         category: str = "general",
                         db_type: str  = "public") -> list[dict]:
        """Ingest all supported files from a directory."""
        reports = []
        for path in Path(directory).iterdir():
            if path.suffix.lower() in self.SUPPORTED_FORMATS:
                report = self.ingest(
                    str(path), tenant_id, category, db_type=db_type
                )
                reports.append(report)
        return reports

    # ── Parsers ──────────────────────────────────────────────────────────

    def _parse(self, path: Path) -> Optional[str]:
        ext    = path.suffix.lower()
        method = self.SUPPORTED_FORMATS.get(ext)
        if not method:
            logger.warning(f"[Ingestion] Unsupported format: {ext}")
            return None
        try:
            return getattr(self, method)(path)
        except Exception as e:
            logger.error(f"[Ingestion] Parse error | file={path.name} | {e}")
            return None

    def _parse_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")

    def _parse_pdf(self, path: Path) -> str:
        try:
            import PyPDF2
            text = []
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text() or "")
            return "\n".join(text)
        except ImportError:
            logger.warning("[Ingestion] PyPDF2 not installed.")
            return ""

    def _parse_docx(self, path: Path) -> str:
        try:
            from docx import Document
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs if p.text)
        except ImportError:
            logger.warning("[Ingestion] python-docx not installed.")
            return ""

    def _parse_xlsx(self, path: Path) -> str:
        try:
            import openpyxl
            wb   = openpyxl.load_workbook(path, read_only=True)
            rows = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    rows.append(
                        " | ".join(str(c) for c in row if c is not None)
                    )
            return "\n".join(rows)
        except ImportError:
            logger.warning("[Ingestion] openpyxl not installed.")
            return ""

    def _parse_csv(self, path: Path) -> str:
        import csv
        rows = []
        with open(path, newline="", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(" | ".join(row))
        return "\n".join(rows)

    def _parse_json(self, path: Path) -> str:
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        return json.dumps(data, indent=2)

    def _parse_xml(self, path: Path) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "xml")
        return soup.get_text(separator="\n", strip=True)

    def _chunk(self, content: str,
                chunk_size: int = 200,
                overlap:    int = 30) -> list[str]:
        """
        Split content into overlapping word-window chunks.
        Overlap prevents context from being cut at chunk boundaries,
        which is a common RAG retrieval quality issue.

        chunk_size = 200 words
        overlap    = 30  words
        """
        words = content.split()
        if not words:
            return []

        chunks = []
        start  = 0
        while start < len(words):
            end   = min(start + chunk_size, len(words))
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            if end >= len(words):
                break
            start += chunk_size - overlap   # slide forward with overlap

        logger.info(
            f"[Ingestion] Chunked into {len(chunks)} chunks "
            f"(size={chunk_size}, overlap={overlap})"
        )
        return chunks
