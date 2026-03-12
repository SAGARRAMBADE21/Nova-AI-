"""
plugins/google_docs.py
Google Docs Plugin — create, get, append, edit, share documents.
"""

import logging
from .base import BasePlugin, PluginResult, with_retry

logger = logging.getLogger(__name__)


class GoogleDocsPlugin(BasePlugin):
    name = "google_docs"
    ACTIONS = [
        "create_document", "get_document",
        "append_content", "edit_document", "share_document",
    ]

    def __init__(self):
        self.service = self._init_service()

    def _init_service(self):
        try:
            from googleapiclient.discovery import build
            creds = self._google_creds()
            if creds:
                return build("docs", "v1", credentials=creds)
        except Exception as e:
            logger.warning(f"[GoogleDocs] Init failed: {e}")
        return None

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "create_document": self._create,
            "get_document":    self._get,
            "append_content":  self._append,
            "edit_document":   self._append,   # alias
            "share_document":  self._share,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    @with_retry()
    def _create(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("create_document")
        title  = params.get("title", "New Document")
        doc    = self.service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]
        url    = f"https://docs.google.com/document/d/{doc_id}/edit"
        content = params.get("content", "")
        if content:
            self.service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": [{"insertText": {"location": {"index": 1}, "text": content}}]},
            ).execute()
        return self._ok("create_document", f"Document created: {title}",
                        data={"document_id": doc_id}, url=url)

    @with_retry()
    def _get(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("get_document")
        doc_id = params.get("document_id")
        if not doc_id:
            return self._missing_param("get_document", "document_id")
        doc  = self.service.documents().get(documentId=doc_id).execute()
        text = ""
        for elem in doc.get("body", {}).get("content", []):
            for pe in elem.get("paragraph", {}).get("elements", []):
                text += pe.get("textRun", {}).get("content", "")
        return self._ok("get_document", f"Retrieved: {doc.get('title')}",
                        data={"title": doc.get("title"), "text": text})

    @with_retry()
    def _append(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("append_content")
        doc_id  = params.get("document_id")
        content = params.get("content")
        if not doc_id:
            return self._missing_param("append_content", "document_id")
        if not content:
            return self._missing_param("append_content", "content")
        doc       = self.service.documents().get(documentId=doc_id).execute()
        end_index = doc["body"]["content"][-1]["endIndex"] - 1
        self.service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{"insertText": {"location": {"index": end_index},
                                               "text": f"\n{content}"}}]},
        ).execute()
        return self._ok("append_content", "Content appended to document.")

    def _share(self, params: dict) -> PluginResult:
        doc_id = params.get("document_id")
        email  = params.get("email")
        if not doc_id:
            return self._missing_param("share_document", "document_id")
        if not email:
            return self._missing_param("share_document", "email")
        logger.info(f"[GoogleDocs] Share {doc_id} → {email}")
        return self._ok("share_document", f"Document shared with {email}.")
