"""
plugins/slack.py
Slack Plugin — send messages, upload files, list channels, reply to threads.
"""

import os
import logging
from .base import BasePlugin, PluginResult, with_retry

logger = logging.getLogger(__name__)


class SlackPlugin(BasePlugin):
    name = "slack"
    ACTIONS = [
        "send_message", "post_to_channel",
        "list_channels", "upload_file",
        "reply_to_thread", "get_channel_history",
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
            logger.warning("[Slack] slack-sdk not installed.")
        return None

    def health_check(self) -> bool:
        if not self.client:
            return False
        try:
            self.client.auth_test()
            return True
        except Exception:
            return False

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "send_message":        self._post,
            "post_to_channel":     self._post,
            "list_channels":       self._list_channels,
            "upload_file":         self._upload_file,
            "reply_to_thread":     self._reply_thread,
            "get_channel_history": self._get_history,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    @with_retry()
    def _post(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("send_message")
        channel = params.get("channel", "#general")
        message = params.get("message") or params.get("text")
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
        if not self.client:
            return self._not_connected("upload_file")
        content  = params.get("content")
        filename = params.get("filename", "file.txt")
        channel  = params.get("channel", "#general")
        if not content:
            return self._missing_param("upload_file", "content")
        result = self.client.files_upload(
            channels=channel,
            filename=filename,
            content=content,
            title=params.get("title", filename),
        )
        return self._ok("upload_file", f"'{filename}' uploaded to {channel}.",
                        url=result["file"].get("permalink"))

    @with_retry()
    def _reply_thread(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("reply_to_thread")
        channel   = params.get("channel")
        thread_ts = params.get("thread_ts")
        message   = params.get("message")
        if not channel:
            return self._missing_param("reply_to_thread", "channel")
        if not thread_ts:
            return self._missing_param("reply_to_thread", "thread_ts")
        if not message:
            return self._missing_param("reply_to_thread", "message")
        result = self.client.chat_postMessage(
            channel=channel, thread_ts=thread_ts, text=message
        )
        return self._ok("reply_to_thread", f"Reply posted in thread.",
                        data={"ts": result["ts"]})

    @with_retry()
    def _get_history(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("get_channel_history")
        channel = params.get("channel")
        if not channel:
            return self._missing_param("get_channel_history", "channel")
        result   = self.client.conversations_history(
            channel=channel, limit=params.get("limit", 20)
        )
        messages = [{"ts": m["ts"], "text": m.get("text", ""), "user": m.get("user")}
                    for m in result.get("messages", [])]
        return self._ok("get_channel_history",
                        f"Retrieved {len(messages)} messages.", data=messages)
