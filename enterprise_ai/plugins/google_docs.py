"""
plugins/google_docs.py
Google Docs Plugin — create, get, append, edit, share documents.

Improvements:
- share_document now calls the Drive Permissions API (was a stub).
- get_document returns structured paragraphs, not just a big text blob.
- replace_text action for find-and-replace in a document.
- Full ActionSchema.
"""

import logging
from .base import BasePlugin, PluginResult, with_retry, ActionSchema, ParamSpec

logger = logging.getLogger(__name__)


class GoogleDocsPlugin(BasePlugin):
    name = "google_docs"
    ACTIONS = [
        "create_document", "get_document",
        "append_content", "edit_document",
        "share_document", "replace_text",
    ]

    def __init__(self):
        self.service     = self._init_docs_service()
        self.drive_svc   = self._init_drive_service()

    def _init_docs_service(self):
        try:
            from googleapiclient.discovery import build
            creds = self._google_creds()
            if creds:
                return build("docs", "v1", credentials=creds)
        except Exception as e:
            logger.warning(f"[GoogleDocs] Docs init failed: {e}")
        return None

    def _init_drive_service(self):
        try:
            from googleapiclient.discovery import build
            creds = self._google_creds()
            if creds:
                return build("drive", "v3", credentials=creds)
        except Exception as e:
            logger.warning(f"[GoogleDocs] Drive init failed: {e}")
        return None

    def health_check(self) -> bool:
        return bool(self.service)

    # ── Schema ────────────────────────────────────────────────────────────

    def get_schema(self):
        return [
            ActionSchema("create_document", "Create a new Google Doc.", [
                ParamSpec("title",   "string", required=False, description="Document title.", default="New Document"),
                ParamSpec("content", "string", required=False, description="Initial text content."),
            ]),
            ActionSchema("get_document", "Retrieve the text content of a Google Doc.", [
                ParamSpec("document_id", "string", required=True, description="Google Docs document ID."),
            ]),
            ActionSchema("append_content", "Append text to the end of a Google Doc.", [
                ParamSpec("document_id", "string", required=True,  description="Google Docs document ID."),
                ParamSpec("content",     "string", required=True,  description="Text to append."),
            ]),
            ActionSchema("edit_document", "Append text to a document (alias for append_content).", [
                ParamSpec("document_id", "string", required=True,  description="Google Docs document ID."),
                ParamSpec("content",     "string", required=True,  description="Text to append."),
            ]),
            ActionSchema("share_document", "Share a Google Doc with another user via Drive permissions.", [
                ParamSpec("document_id", "string", required=True,  description="Google Docs document ID."),
                ParamSpec("email",       "string", required=True,  description="Email to share with."),
                ParamSpec("role",        "string", required=False, description="Permission role.", default="reader",
                          choices=["reader", "commenter", "writer"]),
                ParamSpec("notify",      "boolean", required=False, description="Send notification email.", default=True),
            ]),
            ActionSchema("replace_text", "Find and replace text throughout a Google Doc.", [
                ParamSpec("document_id",   "string",  required=True,  description="Google Docs document ID."),
                ParamSpec("find",          "string",  required=True,  description="Text to find."),
                ParamSpec("replace",       "string",  required=True,  description="Replacement text."),
                ParamSpec("match_case",    "boolean", required=False, description="Case-sensitive search.", default=False),
            ]),
        ]

    # ── Dispatch ──────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "create_document": self._create,
            "get_document":    self._get,
            "append_content":  self._append,
            "edit_document":   self._append,   # alias
            "share_document":  self._share,
            "replace_text":    self._replace_text,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    # ── Actions ───────────────────────────────────────────────────────────

    @with_retry()
    def _create(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("create_document")
        title  = params.get("title", "New Document").strip() or "New Document"
        doc    = self.service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]
        url    = f"https://docs.google.com/document/d/{doc_id}/edit"
        content = params.get("content", "")
        if content:
            self.service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": [{"insertText": {"location": {"index": 1},
                                                   "text": content}}]},
            ).execute()
        return self._ok("create_document", f"Document created: {title}",
                        data={"document_id": doc_id}, url=url)

    @with_retry()
    def _get(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("get_document")
        doc_id = params.get("document_id", "").strip()
        if not doc_id:
            return self._missing_param("get_document", "document_id")
        doc  = self.service.documents().get(documentId=doc_id).execute()
        # Extract structured paragraphs
        paragraphs = []
        for elem in doc.get("body", {}).get("content", []):
            para = elem.get("paragraph")
            if not para:
                continue
            text = "".join(
                r.get("textRun", {}).get("content", "")
                for r in para.get("elements", [])
            )
            if text.strip():
                paragraphs.append(text.rstrip("\n"))
        full_text = "\n".join(paragraphs)
        return self._ok("get_document", f"Retrieved: {doc.get('title')}",
                        data={"title":      doc.get("title"),
                              "text":       full_text,
                              "paragraphs": paragraphs,
                              "url":        f"https://docs.google.com/document/d/{doc_id}/edit"})

    @with_retry()
    def _append(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("append_content")
        doc_id  = params.get("document_id", "").strip()
        content = params.get("content", "")
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

    @with_retry()
    def _share(self, params: dict) -> PluginResult:
        doc_id = params.get("document_id", "").strip()
        email  = params.get("email", "").strip()
        role   = params.get("role", "reader")
        if not doc_id:
            return self._missing_param("share_document", "document_id")
        if not email:
            return self._missing_param("share_document", "email")
        if not self._valid_email(email):
            return self._fail("share_document", f"Invalid email address: '{email}'",
                              error_code="INVALID_PARAMS")
        if role not in ("reader", "commenter", "writer"):
            return self._fail("share_document",
                              f"Invalid role '{role}'. Allowed: reader, commenter, writer",
                              error_code="INVALID_PARAMS")
        # Delegate to Drive Permissions API
        if not self.drive_svc:
            return self._fail("share_document",
                              "Drive service unavailable for sharing. Check credentials.",
                              error_code="NOT_CONNECTED")
        self.drive_svc.permissions().create(
            fileId=doc_id,
            body={"type": "user", "role": role, "emailAddress": email},
            sendNotificationEmail=params.get("notify", True),
        ).execute()
        return self._ok("share_document", f"Document shared with {email} as '{role}'.",
                        url=f"https://docs.google.com/document/d/{doc_id}/edit")

    @with_retry()
    def _replace_text(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("replace_text")
        doc_id  = params.get("document_id", "").strip()
        find    = params.get("find", "")
        replace = params.get("replace", "")
        if not doc_id:
            return self._missing_param("replace_text", "document_id")
        if not find:
            return self._missing_param("replace_text", "find")
        self.service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{
                "replaceAllText": {
                    "containsText": {"text": find,
                                     "matchCase": params.get("match_case", False)},
                    "replaceText": replace,
                }
            }]},
        ).execute()
        return self._ok("replace_text",
                        f"Replaced all occurrences of '{find}' with '{replace}'.")
