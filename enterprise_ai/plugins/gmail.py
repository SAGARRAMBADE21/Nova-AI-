"""
plugins/gmail.py
Gmail Plugin — send, draft, search, read, reply emails and manage labels.

Improvements:
- Email address validation before sending/replying.
- Body decoding in read_email (base64 payload parts).
- cc/bcc support in send_email.
- Rich ActionSchema for every action.
"""

import base64
import logging
import re
from .base import BasePlugin, PluginResult, with_retry, ActionSchema, ParamSpec

logger = logging.getLogger(__name__)


class GmailPlugin(BasePlugin):
    name = "gmail"
    ACTIONS = [
        "send_email", "draft_email",
        "search_emails", "read_email",
        "reply_email", "create_label",
        "list_labels",
    ]

    def __init__(self):
        self.service = self._init_service()

    def _init_service(self):
        try:
            from googleapiclient.discovery import build
            creds = self._google_creds()
            if creds:
                return build("gmail", "v1", credentials=creds)
        except Exception as e:
            logger.warning(f"[Gmail] Init failed: {e}")
        return None

    def health_check(self) -> bool:
        if not self.service:
            return False
        try:
            self.service.users().getProfile(userId="me").execute()
            return True
        except Exception:
            return False

    # ── Schema ────────────────────────────────────────────────────────────

    def get_schema(self):
        return [
            ActionSchema("send_email", "Send an email from the authenticated Gmail account.", [
                ParamSpec("to",      "string",  required=True,  description="Recipient email address."),
                ParamSpec("subject", "string",  required=True,  description="Email subject line."),
                ParamSpec("body",    "string",  required=False, description="Email body (plain text or HTML).", default=""),
                ParamSpec("cc",      "string",  required=False, description="CC recipient email addresses, comma-separated."),
                ParamSpec("bcc",     "string",  required=False, description="BCC recipient email addresses, comma-separated."),
            ]),
            ActionSchema("draft_email", "Save an email as a draft.", [
                ParamSpec("to",      "string",  required=False, description="Recipient email address."),
                ParamSpec("subject", "string",  required=False, description="Email subject.", default="Draft"),
                ParamSpec("body",    "string",  required=False, description="Email body.", default=""),
            ]),
            ActionSchema("search_emails", "Search emails using Gmail query syntax.", [
                ParamSpec("query",       "string",  required=True,  description="Gmail search query, e.g. 'from:boss@example.com is:unread'."),
                ParamSpec("max_results", "integer", required=False, description="Number of results to return.", default=10),
            ]),
            ActionSchema("read_email", "Fetch and decode the full content of an email.", [
                ParamSpec("message_id", "string", required=True, description="Gmail message ID (from search results)."),
            ]),
            ActionSchema("reply_email", "Reply to an existing email thread.", [
                ParamSpec("thread_id", "string", required=True,  description="Gmail thread ID to reply to."),
                ParamSpec("to",        "string", required=True,  description="Recipient email address."),
                ParamSpec("subject",   "string", required=False, description="Reply subject.", default="Re:"),
                ParamSpec("body",      "string", required=False, description="Reply body.", default=""),
            ]),
            ActionSchema("create_label", "Create a new Gmail label.", [
                ParamSpec("name", "string", required=True, description="Label name."),
            ]),
            ActionSchema("list_labels", "List all Gmail labels for the account."),
        ]

    # ── Dispatch ──────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "send_email":    self._send,
            "draft_email":   self._draft,
            "search_emails": self._search,
            "read_email":    self._read,
            "reply_email":   self._reply,
            "create_label":  self._create_label,
            "list_labels":   self._list_labels,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _build_raw(self, to: str, subject: str, body: str,
                   thread_id: str = None, cc: str = None, bcc: str = None) -> dict:
        from email.mime.text import MIMEText
        msg = MIMEText(body, "html" if "<" in body else "plain")
        msg["to"]      = to
        msg["subject"] = subject
        if cc:
            msg["cc"] = cc
        if bcc:
            msg["bcc"] = bcc
        if thread_id:
            msg["In-Reply-To"] = thread_id
            msg["References"]  = thread_id
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        payload = {"raw": raw}
        if thread_id:
            payload["threadId"] = thread_id
        return payload

    @staticmethod
    def _decode_body(payload: dict) -> str:
        """Recursively decode message body from Gmail payload parts."""
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode(errors="replace")
        text = ""
        for part in payload.get("parts", []):
            mime = part.get("mimeType", "")
            if mime in ("text/plain", "text/html"):
                part_data = part.get("body", {}).get("data", "")
                if part_data:
                    text += base64.urlsafe_b64decode(part_data + "==").decode(errors="replace")
        return text.strip()

    # ── Actions ───────────────────────────────────────────────────────────

    @with_retry()
    def _send(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("send_email")
        to      = params.get("to", "").strip()
        subject = params.get("subject", "").strip()
        if not to:
            return self._missing_param("send_email", "to")
        if not subject:
            return self._missing_param("send_email", "subject")
        if not self._valid_email(to):
            return self._fail("send_email", f"Invalid email address: '{to}'",
                              error_code="INVALID_PARAMS")
        msg    = self._build_raw(to, subject, params.get("body", ""),
                                 cc=params.get("cc"), bcc=params.get("bcc"))
        result = self.service.users().messages().send(userId="me", body=msg).execute()
        return self._ok("send_email", f"Email sent to {to}.",
                        data={"message_id": result["id"]})

    @with_retry()
    def _draft(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("draft_email")
        to = params.get("to", "").strip()
        if to and not self._valid_email(to):
            return self._fail("draft_email", f"Invalid email address: '{to}'",
                              error_code="INVALID_PARAMS")
        msg    = self._build_raw(to,
                                 params.get("subject", "Draft"),
                                 params.get("body", ""))
        result = self.service.users().drafts().create(
            userId="me", body={"message": msg}
        ).execute()
        return self._ok("draft_email", f"Draft created." + (f" To: {to}" if to else ""),
                        data={"draft_id": result["id"]})

    @with_retry()
    def _search(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("search_emails")
        query = params.get("query", "").strip()
        if not query:
            return self._missing_param("search_emails", "query")
        max_results = min(int(params.get("max_results", 10)), 500)
        result   = self.service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
        messages = result.get("messages", [])
        return self._ok("search_emails", f"Found {len(messages)} emails.", data=messages)

    @with_retry()
    def _read(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("read_email")
        msg_id = params.get("message_id", "").strip()
        if not msg_id:
            return self._missing_param("read_email", "message_id")
        msg     = self.service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()
        headers = {h["name"]: h["value"]
                   for h in msg.get("payload", {}).get("headers", [])}
        body    = self._decode_body(msg.get("payload", {}))
        return self._ok("read_email", f"Email from {headers.get('From', 'unknown')}",
                        data={"from":    headers.get("From"),
                              "to":      headers.get("To"),
                              "subject": headers.get("Subject"),
                              "date":    headers.get("Date"),
                              "snippet": msg.get("snippet", ""),
                              "body":    body or msg.get("snippet", "")})

    @with_retry()
    def _reply(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("reply_email")
        thread_id = params.get("thread_id", "").strip()
        to        = params.get("to", "").strip()
        if not thread_id:
            return self._missing_param("reply_email", "thread_id")
        if not to:
            return self._missing_param("reply_email", "to")
        if not self._valid_email(to):
            return self._fail("reply_email", f"Invalid email address: '{to}'",
                              error_code="INVALID_PARAMS")
        msg    = self._build_raw(to, params.get("subject", "Re:"),
                                 params.get("body", ""), thread_id=thread_id)
        result = self.service.users().messages().send(userId="me", body=msg).execute()
        return self._ok("reply_email", f"Reply sent to {to}.",
                        data={"message_id": result["id"]})

    @with_retry()
    def _create_label(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("create_label")
        name = params.get("name", "").strip()
        if not name:
            return self._missing_param("create_label", "name")
        label = self.service.users().labels().create(
            userId="me",
            body={"name": name, "labelListVisibility": "labelShow",
                  "messageListVisibility": "show"},
        ).execute()
        return self._ok("create_label", f"Label '{name}' created.",
                        data={"label_id": label["id"]})

    @with_retry()
    def _list_labels(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("list_labels")
        result = self.service.users().labels().list(userId="me").execute()
        labels = [{"id": l["id"], "name": l["name"]}
                  for l in result.get("labels", [])]
        return self._ok("list_labels", f"Found {len(labels)} labels.", data=labels)
