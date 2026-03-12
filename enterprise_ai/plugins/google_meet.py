"""
plugins/google_meet.py
Google Meet Plugin — creates real Meet links via Calendar API.
"""

import logging
from .base import BasePlugin, PluginResult
from .google_calendar import GoogleCalendarPlugin

logger = logging.getLogger(__name__)


class GoogleMeetPlugin(BasePlugin):
    name = "google_meet"
    ACTIONS = ["create_meeting", "schedule_call", "create_link", "share_invite"]

    def __init__(self):
        self._calendar = GoogleCalendarPlugin()

    def health_check(self) -> bool:
        return self._calendar.health_check()

    def execute(self, action: str, params: dict) -> PluginResult:
        if action not in self.ACTIONS:
            return self._unknown_action(action)
        params["add_meet_link"] = True
        result = self._calendar._create_event(params)
        if result.success:
            meet_link = (result.data or {}).get("meet_link", "")
            return self._ok(action,
                            f"Google Meet scheduled: {params.get('title', 'Meeting')}",
                            data=result.data,
                            url=meet_link or result.url)
        return self._fail(action, result.message, error_code=result.error_code or "ERROR")
