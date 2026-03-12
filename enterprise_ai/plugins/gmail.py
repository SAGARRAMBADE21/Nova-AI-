"""
plugins/gmail.py
Gmail Plugin — send, draft, search, read, reply emails and manage labels.
"""

import logging
from .base import BasePlugin, PluginResult, with_retry

logger = logging.getLogger(__name__)


class GmailPlugin(BasePlugin):
    name = "gmail"
    ACTIONS = [
        "send_email", "draft_email",
        "search_emails", "read_email",
        "reply_email", "create_label",
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

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "send_email":    self._send,
            "draft_email":   self._draft,
            "search_emails": self._search,
            "read_email":    self._read,
            "reply_email":   self._reply,
            "create_label":  self._create_label,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    def _build_raw(self, to: str, subject: str, body: str,
                   thread_id: str = None) -> dict:
        import base64
        from email.mime.text import MIMEText
        msg = MIMEText(body, "html" if "<" in body else "plain")
        msg["to"]      = to
        msg["subject"] = subject
        if thread_id:
            msg["In-Reply-To"] = thread_id
            msg["References"]  = thread_id
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        payload = {"raw": raw}
        if thread_id:
            payload["threadId"] = thread_id
        return payload

    @with_retry()
    def _send(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("send_email")
        to      = params.get("to")
        subject = params.get("subject")
        if not to:
            return self._missing_param("send_email", "to")
        if not subject:
            return self._missing_param("send_email", "subject")
        msg    = self._build_raw(to, subject, params.get("body", ""))
        result = self.service.users().messages().send(userId="me", body=msg).execute()
        return self._ok("send_email", f"Email sent to {to}.",
                        data={"message_id": result["id"]})

    @with_retry()
    def _draft(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("draft_email")
        msg    = self._build_raw(params.get("to", ""),
                                 params.get("subject", "Draft"),
                                 params.get("body", ""))
        result = self.service.users().drafts().create(
            userId="me", body={"message": msg}
        ).execute()
        return self._ok("draft_email", f"Draft created for {params.get('to')}.",
                        data={"draft_id": result["id"]})

    @with_retry()
    def _search(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("search_emails")
        query = params.get("query")
        if not query:
            return self._missing_param("search_emails", "query")
        result   = self.service.users().messages().list(
            userId="me", q=query, maxResults=params.get("max_results", 10)
        ).execute()
        messages = result.get("messages", [])
        return self._ok("search_emails", f"Found {len(messages)} emails.", data=messages)

    @with_retry()
    def _read(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("read_email")
        msg_id = params.get("message_id")
        if not msg_id:
            return self._missing_param("read_email", "message_id")
        msg     = self.service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        return self._ok("read_email", f"Email from {headers.get('From')}",
                        data={"from": headers.get("From"),
                              "subject": headers.get("Subject"),
                              "date": headers.get("Date"),
                              "snippet": msg.get("snippet", "")})

    @with_retry()
    def _reply(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("reply_email")
        thread_id = params.get("thread_id")
        to        = params.get("to")
        if not thread_id:
            return self._missing_param("reply_email", "thread_id")
        if not to:
            return self._missing_param("reply_email", "to")
        msg    = self._build_raw(to, params.get("subject", "Re:"),
                                 params.get("body", ""), thread_id=thread_id)
        result = self.service.users().messages().send(userId="me", body=msg).execute()
        return self._ok("reply_email", f"Reply sent to {to}.",
                        data={"message_id": result["id"]})

    @with_retry()
    def _create_label(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("create_label")
        name = params.get("name")
        if not name:
            return self._missing_param("create_label", "name")
        label = self.service.users().labels().create(
            userId="me",
            body={"name": name, "labelListVisibility": "labelShow",
                  "messageListVisibility": "show"},
        ).execute()
        return self._ok("create_label", f"Label '{name}' created.",
                        data={"label_id": label["id"]})
