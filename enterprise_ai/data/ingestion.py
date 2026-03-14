"""
data/ingestion.py
Real-Time Admin Data Ingestion (24/7)
Supports: PDF, DOCX, XLSX, CSV, TXT, JSON, XML, URLs
Pipeline: Upload → Lakera Scan → Parse → Chunk → Embed → Graph Update
"""

import os
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class DataIngestionPipeline:

    SUPPORTED_FORMATS = {
        ".pdf": "_parse_pdf",
        ".docx": "_parse_docx",
        ".xlsx": "_parse_xlsx",
        ".csv": "_parse_csv",
        ".txt": "_parse_text",
        ".json": "_parse_json",
        ".xml": "_parse_xml",
        ".md": "_parse_text",
    }

    def __init__(self, vector_store, knowledge_graph, lakera_guard=None):
        self.vector_store    = vector_store
        self.knowledge_graph = knowledge_graph
        self.lakera          = lakera_guard

    # ── Main entry point ─────────────────────────────────────────────────

    def ingest(self, file_path: str, category: str = "general",
               uploaded_by: str = "admin",
               db: str = "public") -> dict:
        """
        Full ingestion pipeline for a single file.
        db='public'  → stored in public_knowledge  (visible to all employees)
        db='private' → stored in private_knowledge (visible to Team Lead, Manager, Admin only)
        Returns ingestion report.
        """
        path      = Path(file_path)
        timestamp = datetime.utcnow().isoformat()

        logger.info(f"[Ingestion] Starting | file={path.name} | db={db} | category={category}")

        # 1. Parse content
        content = self._parse(path)
        if not content:
            return {"status": "failed", "reason": "Could not parse file", "file": path.name}

        # 2. Lakera Guard scan
        if self.lakera:
            result = self.lakera.scan_document(content[:2000], path.name, "admin", "ingestion")
            if result.flagged:
                logger.warning(f"[Ingestion] Lakera blocked file | file={path.name} | threat={result.threat.value}")
                return {"status": "blocked", "reason": result.message, "file": path.name}

        # 3. Chunk
        chunks = self._chunk(content)

        # 4. Embed into correct vector store collection
        for i, chunk in enumerate(chunks):
            self.vector_store.add_document(
                content   = chunk,
                source    = path.name,
                timestamp = timestamp,
                category  = category,
                db        = db,
            )

        # 5. Update knowledge graph
        self.knowledge_graph.update_from_document(content, path.name)

        report = {
            "status":      "success",
            "file":        path.name,
            "chunks":      len(chunks),
            "category":    category,
            "uploaded_by": uploaded_by,
            "timestamp":   timestamp,
        }
        logger.info(f"[Ingestion] Complete | {report}")
        return report

    def ingest_directory(self, directory: str, category: str = "general") -> list[dict]:
        """Ingest all supported files from a directory."""
        reports = []
        for path in Path(directory).iterdir():
            if path.suffix.lower() in self.SUPPORTED_FORMATS:
                report = self.ingest(str(path), category)
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
            logger.error(f"[Ingestion] Parse error | file={path.name} | error={e}")
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
            doc = Document(path)
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
                    rows.append(" | ".join(str(c) for c in row if c is not None))
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

    def _chunk(self, content: str, chunk_size: int = 500) -> list[str]:
        words  = content.split()
        return [
            " ".join(words[i:i + chunk_size])
            for i in range(0, len(words), chunk_size)
        ]
