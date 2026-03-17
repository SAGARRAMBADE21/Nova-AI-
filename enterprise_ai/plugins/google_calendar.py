"""
plugins/google_calendar.py
Google Calendar Plugin — list, create, update, delete events with Meet links.

Improvements:
- ACTIONS list now includes 'schedule_meeting' (was in dispatch map but not ACTIONS).
- ISO-8601 datetime validation for start/end.
- get_event action added to fetch a single event by ID.
- Full ActionSchema.
"""

import time
import logging
import re
from .base import BasePlugin, PluginResult, with_retry, ActionSchema, ParamSpec

logger = logging.getLogger(__name__)

_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def _valid_iso(value: str) -> bool:
    return bool(_ISO_RE.match(value))


class GoogleCalendarPlugin(BasePlugin):
    name = "google_calendar"
    ACTIONS = [
        "list_events", "create_event",
        "update_event", "delete_event",
        "set_reminder", "schedule_meeting",
        "get_event",
    ]

    def __init__(self):
        self._service = None

    def _ensure_service(self):
        """Lazy-init / re-init the Calendar service with fresh credentials."""
        if not self._service:
            self._service = self._build_google_service("calendar", "v3")
        return self._service

    @property
    def service(self):
        return self._ensure_service()

    def health_check(self) -> bool:
        svc = self._ensure_service()
        if not svc:
            return False
        try:
            svc.calendarList().list(maxResults=1).execute()
            return True
        except Exception:
            self._service = None  # force re-init on next call
            return False

    # ── Schema ────────────────────────────────────────────────────────────

    def get_schema(self):
        _event_params = [
            ParamSpec("start",               "string",  required=True,  description="Start datetime in ISO 8601 format, e.g. '2025-06-20T10:00:00'."),
            ParamSpec("end",                 "string",  required=True,  description="End datetime in ISO 8601 format."),
            ParamSpec("title",               "string",  required=False, description="Event title.", default="Meeting"),
            ParamSpec("description",         "string",  required=False, description="Event description."),
            ParamSpec("location",            "string",  required=False, description="Physical or virtual location."),
            ParamSpec("timezone",            "string",  required=False, description="IANA timezone name.", default="UTC"),
            ParamSpec("attendees",           "list",    required=False, description="List of attendee email addresses."),
            ParamSpec("add_meet_link",       "boolean", required=False, description="Generate a Google Meet link.", default=False),
            ParamSpec("reminder_email_min",  "integer", required=False, description="Email reminder minutes before event.", default=60),
            ParamSpec("reminder_popup_min",  "integer", required=False, description="Popup reminder minutes before event.", default=10),
        ]
        return [
            ActionSchema("list_events", "List upcoming calendar events.", [
                ParamSpec("time_min",    "string",  required=False, description="ISO 8601 lower bound for events. Defaults to now."),
                ParamSpec("max_results", "integer", required=False, description="Maximum number of events to return.", default=10),
            ]),
            ActionSchema("create_event",     "Create a new calendar event.", _event_params),
            ActionSchema("set_reminder",     "Create a reminder as a calendar event.", _event_params),
            ActionSchema("schedule_meeting", "Schedule a meeting (alias for create_event).", _event_params),
            ActionSchema("update_event", "Update an existing calendar event.", [
                ParamSpec("event_id",    "string", required=True,  description="Google Calendar event ID."),
                ParamSpec("title",       "string", required=False, description="New event title."),
                ParamSpec("start",       "string", required=False, description="New start datetime (ISO 8601)."),
                ParamSpec("end",         "string", required=False, description="New end datetime (ISO 8601)."),
                ParamSpec("description", "string", required=False, description="New description."),
            ]),
            ActionSchema("delete_event", "Delete a calendar event.", [
                ParamSpec("event_id", "string", required=True, description="Google Calendar event ID."),
            ]),
            ActionSchema("get_event", "Get details of a specific calendar event.", [
                ParamSpec("event_id", "string", required=True, description="Google Calendar event ID."),
            ]),
        ]

    # ── Dispatch ──────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "list_events":      self._list_events,
            "create_event":     self._create_event,
            "update_event":     self._update_event,
            "delete_event":     self._delete_event,
            "set_reminder":     self._create_event,
            "schedule_meeting": self._create_event,
            "get_event":        self._get_event,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    # ── Actions ───────────────────────────────────────────────────────────

    @with_retry()
    def _list_events(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("list_events")
        from datetime import datetime, timezone
        time_min    = params.get("time_min", datetime.now(timezone.utc).isoformat())
        max_results = min(int(params.get("max_results", 10)), 250)
        result = self.service.events().list(
            calendarId="primary",
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = result.get("items", [])
        simplified = [
            {
                "id":       e.get("id"),
                "title":    e.get("summary"),
                "start":    e.get("start", {}).get("dateTime") or e.get("start", {}).get("date"),
                "end":      e.get("end",   {}).get("dateTime") or e.get("end",   {}).get("date"),
                "location": e.get("location"),
                "link":     e.get("hangoutLink"),
                "url":      e.get("htmlLink"),
            }
            for e in events
        ]
        return self._ok("list_events", f"Found {len(events)} upcoming events.", data=simplified)

    @with_retry()
    def _create_event(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("create_event")
        start = params.get("start", "")
        end   = params.get("end", "")
        if not start:
            return self._missing_param("create_event", "start")
        if not end:
            return self._missing_param("create_event", "end")
        if not _valid_iso(start):
            return self._fail("create_event",
                              f"'start' must be ISO 8601 datetime, got: '{start}'",
                              error_code="INVALID_PARAMS")
        if not _valid_iso(end):
            return self._fail("create_event",
                              f"'end' must be ISO 8601 datetime, got: '{end}'",
                              error_code="INVALID_PARAMS")
        tz    = params.get("timezone", "UTC")
        attendees_raw = params.get("attendees", [])
        # Validate attendee emails
        invalid_emails = [e for e in attendees_raw if not self._valid_email(e)]
        if invalid_emails:
            return self._fail("create_event",
                              f"Invalid attendee email(s): {invalid_emails}",
                              error_code="INVALID_PARAMS")
        event = {
            "summary":     params.get("title", "Meeting"),
            "description": params.get("description", ""),
            "location":    params.get("location", ""),
            "start":       {"dateTime": start, "timeZone": tz},
            "end":         {"dateTime": end,   "timeZone": tz},
            "attendees":   [{"email": e} for e in attendees_raw],
            "reminders":   {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": params.get("reminder_email_min", 60)},
                    {"method": "popup", "minutes": params.get("reminder_popup_min", 10)},
                ],
            },
        }
        if params.get("add_meet_link", False):
            event["conferenceData"] = {
                "createRequest": {"requestId": f"meet-{int(time.time())}"}
            }
        result = self.service.events().insert(
            calendarId="primary", body=event,
            conferenceDataVersion=1 if params.get("add_meet_link") else 0,
        ).execute()
        meet_link = result.get("hangoutLink", "")
        return self._ok("create_event", f"Event '{params.get('title', 'Meeting')}' created.",
                        data={"event_id": result["id"], "meet_link": meet_link},
                        url=result.get("htmlLink"))

    @with_retry()
    def _update_event(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("update_event")
        event_id = params.get("event_id", "").strip()
        if not event_id:
            return self._missing_param("update_event", "event_id")
        # Validate updated datetimes if provided
        for field in ("start", "end"):
            val = params.get(field)
            if val and not _valid_iso(val):
                return self._fail("update_event",
                                  f"'{field}' must be ISO 8601 datetime, got: '{val}'",
                                  error_code="INVALID_PARAMS")
        event = self.service.events().get(calendarId="primary", eventId=event_id).execute()
        if params.get("title"):
            event["summary"] = params["title"]
        if params.get("start"):
            event["start"]["dateTime"] = params["start"]
        if params.get("end"):
            event["end"]["dateTime"] = params["end"]
        if params.get("description"):
            event["description"] = params["description"]
        updated = self.service.events().update(
            calendarId="primary", eventId=event_id, body=event
        ).execute()
        return self._ok("update_event", "Event updated.", url=updated.get("htmlLink"))

    @with_retry()
    def _delete_event(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("delete_event")
        event_id = params.get("event_id", "").strip()
        if not event_id:
            return self._missing_param("delete_event", "event_id")
        self.service.events().delete(calendarId="primary", eventId=event_id).execute()
        return self._ok("delete_event", f"Event {event_id} deleted.")

    @with_retry()
    def _get_event(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("get_event")
        event_id = params.get("event_id", "").strip()
        if not event_id:
            return self._missing_param("get_event", "event_id")
        event = self.service.events().get(calendarId="primary", eventId=event_id).execute()
        data  = {
            "id":          event.get("id"),
            "title":       event.get("summary"),
            "start":       event.get("start", {}).get("dateTime"),
            "end":         event.get("end",   {}).get("dateTime"),
            "description": event.get("description"),
            "location":    event.get("location"),
            "meet_link":   event.get("hangoutLink"),
            "attendees":   [a.get("email") for a in event.get("attendees", [])],
        }
        return self._ok("get_event", f"Event: {event.get('summary', event_id)}",
                        data=data, url=event.get("htmlLink"))
