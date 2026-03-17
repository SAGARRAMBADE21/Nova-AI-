"""
plugins/google_meet.py
Google Meet Plugin — creates real Meet links via Calendar API.

Improvements:
- get_meeting_info action: retrieves Calendar event + extracts Meet link.
- cancel_meeting action: deletes the underlying calendar event.
- list_upcoming_meetings: lists events that have a hangoutLink.
- Full ActionSchema.
"""

import logging
from .base import BasePlugin, PluginResult, ActionSchema, ParamSpec
from .google_calendar import GoogleCalendarPlugin

logger = logging.getLogger(__name__)


class GoogleMeetPlugin(BasePlugin):
    name = "google_meet"
    ACTIONS = [
        "create_meeting", "schedule_call",
        "create_link", "share_invite",
        "get_meeting_info", "cancel_meeting",
        "list_upcoming_meetings",
    ]

    def __init__(self):
        self._calendar = GoogleCalendarPlugin()

    def health_check(self) -> bool:
        return self._calendar.health_check()

    # ── Schema ────────────────────────────────────────────────────────────

    def get_schema(self):
        _meeting_params = [
            ParamSpec("start",       "string",  required=True,  description="Start datetime in ISO 8601 format."),
            ParamSpec("end",         "string",  required=True,  description="End datetime in ISO 8601 format."),
            ParamSpec("title",       "string",  required=False, description="Meeting title.", default="Meeting"),
            ParamSpec("description", "string",  required=False, description="Meeting description."),
            ParamSpec("timezone",    "string",  required=False, description="IANA timezone.", default="UTC"),
            ParamSpec("attendees",   "list",    required=False, description="List of attendee email addresses."),
        ]
        return [
            ActionSchema("create_meeting",    "Schedule a new Google Meet video call.", _meeting_params),
            ActionSchema("schedule_call",     "Alias for create_meeting.", _meeting_params),
            ActionSchema("create_link",       "Create a Meet link for a meeting.", _meeting_params),
            ActionSchema("share_invite",      "Create a meeting and share the invite link.", _meeting_params),
            ActionSchema("get_meeting_info",  "Get details of an existing Meet event.", [
                ParamSpec("event_id", "string", required=True, description="Google Calendar event ID."),
            ]),
            ActionSchema("cancel_meeting", "Cancel a scheduled meeting.", [
                ParamSpec("event_id", "string", required=True, description="Google Calendar event ID to cancel."),
            ]),
            ActionSchema("list_upcoming_meetings", "List upcoming meetings that have a Google Meet link.", [
                ParamSpec("max_results", "integer", required=False, description="Max meetings to return.", default=10),
            ]),
        ]

    # ── Dispatch ──────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> PluginResult:
        if action not in self.ACTIONS:
            return self._unknown_action(action)
        if action in ("create_meeting", "schedule_call", "create_link", "share_invite"):
            return self._create_meeting(action, params)
        if action == "get_meeting_info":
            return self._get_meeting_info(params)
        if action == "cancel_meeting":
            return self._cancel_meeting(params)
        if action == "list_upcoming_meetings":
            return self._list_upcoming(params)
        return self._unknown_action(action)

    # ── Actions ───────────────────────────────────────────────────────────

    def _create_meeting(self, action: str, params: dict) -> PluginResult:
        params["add_meet_link"] = True
        result = self._calendar._create_event(params)
        if result.success:
            meet_link = (result.data or {}).get("meet_link", "")
            return self._ok(action,
                            f"Google Meet scheduled: {params.get('title', 'Meeting')}",
                            data=result.data,
                            url=meet_link or result.url)
        return self._fail(action, result.message, error_code=result.error_code or "ERROR")

    def _get_meeting_info(self, params: dict) -> PluginResult:
        result = self._calendar._get_event(params)
        if result.success:
            data      = result.data or {}
            meet_link = data.get("meet_link")
            return self._ok("get_meeting_info",
                            f"Meeting: {data.get('title', params.get('event_id'))}",
                            data=data,
                            url=meet_link or result.url)
        return self._fail("get_meeting_info", result.message,
                          error_code=result.error_code or "ERROR")

    def _cancel_meeting(self, params: dict) -> PluginResult:
        result = self._calendar._delete_event(params)
        if result.success:
            return self._ok("cancel_meeting",
                            f"Meeting {params.get('event_id')} cancelled.")
        return self._fail("cancel_meeting", result.message,
                          error_code=result.error_code or "ERROR")

    def _list_upcoming(self, params: dict) -> PluginResult:
        result = self._calendar._list_events(params)
        if not result.success:
            return self._fail("list_upcoming_meetings", result.message,
                              error_code=result.error_code or "ERROR")
        # Filter for events with a Meet link
        meetings = [e for e in (result.data or []) if e.get("link")]
        return self._ok("list_upcoming_meetings",
                        f"Found {len(meetings)} upcoming meetings with Meet links.",
                        data=meetings)
