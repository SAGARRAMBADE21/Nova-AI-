"""
plugins/slack.py
Slack Plugin — send messages, upload files, list channels, reply to threads.

Improvements:
- files_upload (deprecated Nov 2025) replaced with the new 3-step
  files.getUploadURLExternal → PUT → files.completeUploadExternal workflow.
- send_dm action added (direct message via user ID or email).
- get_user_info action added.
- Full ActionSchema.
"""

import os
import logging
import requests as _requests
from .base import BasePlugin, PluginResult, with_retry, ActionSchema, ParamSpec

logger = logging.getLogger(__name__)


class SlackPlugin(BasePlugin):
    name = "slack"
    ACTIONS = [
        "send_message", "post_to_channel",
        "list_channels", "upload_file",
        "reply_to_thread", "get_channel_history",
        "send_dm", "get_user_info",
    ]

    def __init__(self):
        self.client = self._init_client()

    def _init_client(self):
        try:
            from slack_sdk import WebClient
            token = os.getenv("SLACK_BOT_TOKEN", "")
            if token and token != "your_slack_bot_token":
                return WebClient(token=token)
        except ImportError:
            logger.warning("[Slack] slack-sdk not installed. Run: pip install slack-sdk")
        return None

    def health_check(self) -> bool:
        if not self.client:
            return False
        try:
            self.client.auth_test()
            return True
        except Exception:
            return False

    # ── Schema ────────────────────────────────────────────────────────────

    def get_schema(self):
        return [
            ActionSchema("send_message", "Post a message to a Slack channel.", [
                ParamSpec("channel", "string", required=True,  description="Channel name or ID, e.g. '#general' or 'C012AB3CD'."),
                ParamSpec("message", "string", required=True,  description="Message text or fallback text when using blocks."),
                ParamSpec("blocks",  "list",   required=False, description="Optional Slack Block Kit blocks payload."),
            ]),
            ActionSchema("post_to_channel", "Alias for send_message.", [
                ParamSpec("channel", "string", required=True,  description="Channel name or ID."),
                ParamSpec("message", "string", required=True,  description="Message text."),
            ]),
            ActionSchema("list_channels", "List all public Slack channels.", [
                ParamSpec("limit", "integer", required=False, description="Max channels to return.", default=50),
            ]),
            ActionSchema("upload_file", "Upload a file to a Slack channel (new API).", [
                ParamSpec("content",  "string", required=True,  description="Text content to upload."),
                ParamSpec("filename", "string", required=False, description="Filename.", default="file.txt"),
                ParamSpec("channel",  "string", required=True,  description="Channel ID to share the file in (not channel name)."),
                ParamSpec("title",    "string", required=False, description="File title."),
            ]),
            ActionSchema("reply_to_thread", "Reply in a Slack thread.", [
                ParamSpec("channel",   "string", required=True, description="Channel ID or name."),
                ParamSpec("thread_ts", "string", required=True, description="Timestamp of the parent message."),
                ParamSpec("message",   "string", required=True, description="Reply text."),
            ]),
            ActionSchema("get_channel_history", "Retrieve recent messages from a channel.", [
                ParamSpec("channel", "string",  required=True,  description="Channel ID."),
                ParamSpec("limit",   "integer", required=False, description="Number of messages to retrieve.", default=20),
            ]),
            ActionSchema("send_dm", "Send a direct message to a Slack user.", [
                ParamSpec("user_id", "string", required=True,  description="Slack user ID (e.g. 'U012AB3CD')."),
                ParamSpec("message", "string", required=True,  description="Message text."),
            ]),
            ActionSchema("get_user_info", "Get information about a Slack user.", [
                ParamSpec("user_id", "string", required=True, description="Slack user ID."),
            ]),
        ]

    # ── Dispatch ──────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "send_message":        self._post,
            "post_to_channel":     self._post,
            "list_channels":       self._list_channels,
            "upload_file":         self._upload_file,
            "reply_to_thread":     self._reply_thread,
            "get_channel_history": self._get_history,
            "send_dm":             self._send_dm,
            "get_user_info":       self._get_user_info,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    # ── Actions ───────────────────────────────────────────────────────────

    @with_retry()
    def _post(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("send_message")
        channel = params.get("channel", "").strip()
        message = params.get("message") or params.get("text", "")
        if not channel:
            return self._missing_param("send_message", "channel")
        if not message:
            return self._missing_param("send_message", "message")
        result = self.client.chat_postMessage(
            channel=channel,
            text=message,
            blocks=params.get("blocks"),
        )
        return self._ok("send_message", f"Message posted to {channel}.",
                        data={"ts": result["ts"], "channel": result["channel"]})

    @with_retry()
    def _list_channels(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("list_channels")
        result   = self.client.conversations_list(limit=params.get("limit", 50))
        channels = [{"id": c["id"], "name": c["name"], "is_private": c["is_private"]}
                    for c in result.get("channels", [])]
        return self._ok("list_channels", f"Found {len(channels)} channels.", data=channels)

    @with_retry()
    def _upload_file(self, params: dict) -> PluginResult:
        """Upload a file using the new Slack external upload API.

        Steps:
        1. files.getUploadURLExternal  → upload_url + file_id
        2. PUT upload_url with raw content bytes
        3. files.completeUploadExternal → finalise & share
        """
        if not self.client:
            return self._not_connected("upload_file")
        content  = params.get("content", "")
        filename = params.get("filename", "file.txt").strip()
        channel  = params.get("channel", "").strip()
        title    = params.get("title", filename)
        if not content:
            return self._missing_param("upload_file", "content")
        if not channel:
            return self._missing_param("upload_file", "channel")

        encoded = content.encode("utf-8")
        # Step 1 – get upload URL
        step1 = self.client.files_getUploadURLExternal(
            filename=filename,
            length=len(encoded),
        )
        upload_url = step1["upload_url"]
        file_id    = step1["file_id"]

        # Step 2 – upload the raw bytes
        put_resp = _requests.put(
            upload_url,
            data=encoded,
            headers={"Content-Type": "application/octet-stream"},
            timeout=30,
        )
        put_resp.raise_for_status()

        # Step 3 – complete the upload and share to channel
        self.client.files_completeUploadExternal(
            files=[{"id": file_id, "title": title}],
            channel_id=channel,
        )
        return self._ok("upload_file", f"'{filename}' uploaded and shared to channel {channel}.",
                        data={"file_id": file_id})

    @with_retry()
    def _reply_thread(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("reply_to_thread")
        channel   = params.get("channel", "").strip()
        thread_ts = params.get("thread_ts", "").strip()
        message   = params.get("message", "").strip()
        if not channel:
            return self._missing_param("reply_to_thread", "channel")
        if not thread_ts:
            return self._missing_param("reply_to_thread", "thread_ts")
        if not message:
            return self._missing_param("reply_to_thread", "message")
        result = self.client.chat_postMessage(
            channel=channel, thread_ts=thread_ts, text=message
        )
        return self._ok("reply_to_thread", "Reply posted in thread.",
                        data={"ts": result["ts"]})

    @with_retry()
    def _get_history(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("get_channel_history")
        channel = params.get("channel", "").strip()
        if not channel:
            return self._missing_param("get_channel_history", "channel")
        result   = self.client.conversations_history(
            channel=channel, limit=params.get("limit", 20)
        )
        messages = [{"ts": m["ts"], "text": m.get("text", ""), "user": m.get("user")}
                    for m in result.get("messages", [])]
        return self._ok("get_channel_history",
                        f"Retrieved {len(messages)} messages.", data=messages)

    @with_retry()
    def _send_dm(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("send_dm")
        user_id = params.get("user_id", "").strip()
        message = params.get("message", "").strip()
        if not user_id:
            return self._missing_param("send_dm", "user_id")
        if not message:
            return self._missing_param("send_dm", "message")
        # Open a DM channel, then post
        conv    = self.client.conversations_open(users=user_id)
        channel = conv["channel"]["id"]
        result  = self.client.chat_postMessage(channel=channel, text=message)
        return self._ok("send_dm", f"DM sent to user {user_id}.",
                        data={"ts": result["ts"], "channel": channel})

    @with_retry()
    def _get_user_info(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("get_user_info")
        user_id = params.get("user_id", "").strip()
        if not user_id:
            return self._missing_param("get_user_info", "user_id")
        result = self.client.users_info(user=user_id)
        user   = result.get("user", {})
        profile = user.get("profile", {})
        return self._ok("get_user_info", f"User: {profile.get('real_name', user_id)}",
                        data={"id":          user.get("id"),
                              "name":        user.get("name"),
                              "real_name":   profile.get("real_name"),
                              "email":       profile.get("email"),
                              "title":       profile.get("title"),
                              "is_admin":    user.get("is_admin"),
                              "is_bot":      user.get("is_bot")})
