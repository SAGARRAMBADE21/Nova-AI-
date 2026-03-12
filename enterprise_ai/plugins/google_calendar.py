"""
plugins/google_calendar.py
Google Calendar Plugin — list, create, update, delete events with Meet links.
"""

import time
import logging
from .base import BasePlugin, PluginResult, with_retry

logger = logging.getLogger(__name__)


class GoogleCalendarPlugin(BasePlugin):
    name = "google_calendar"
    ACTIONS = [
        "list_events", "create_event",
        "update_event", "delete_event", "set_reminder",
    ]

    def __init__(self):
        self.service = self._init_service()

    def _init_service(self):
        try:
            from googleapiclient.discovery import build
            creds = self._google_creds()
            if creds:
                return build("calendar", "v3", credentials=creds)
        except Exception as e:
            logger.warning(f"[GoogleCalendar] Init failed: {e}")
        return None

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "list_events":      self._list_events,
            "create_event":     self._create_event,
            "update_event":     self._update_event,
            "delete_event":     self._delete_event,
            "set_reminder":     self._create_event,
            "schedule_meeting": self._create_event,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    @with_retry()
    def _list_events(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("list_events")
        from datetime import datetime, timezone
        time_min    = params.get("time_min", datetime.now(timezone.utc).isoformat())
        max_results = params.get("max_results", 10)
        result = self.service.events().list(
            calendarId="primary",
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = result.get("items", [])
        return self._ok("list_events", f"Found {len(events)} upcoming events.", data=events)

    @with_retry()
    def _create_event(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("create_event")
        start = params.get("start")
        end   = params.get("end")
        if not start:
            return self._missing_param("create_event", "start")
        if not end:
            return self._missing_param("create_event", "end")
        tz    = params.get("timezone", "UTC")
        event = {
            "summary":     params.get("title", "Meeting"),
            "description": params.get("description", ""),
            "location":    params.get("location", ""),
            "start":       {"dateTime": start, "timeZone": tz},
            "end":         {"dateTime": end,   "timeZone": tz},
            "attendees":   [{"email": e} for e in params.get("attendees", [])],
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
        return self._ok("create_event", f"Event '{params.get('title')}' created.",
                        data={"event_id": result["id"], "meet_link": meet_link},
                        url=result.get("htmlLink"))

    @with_retry()
    def _update_event(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("update_event")
        event_id = params.get("event_id")
        if not event_id:
            return self._missing_param("update_event", "event_id")
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
        event_id = params.get("event_id")
        if not event_id:
            return self._missing_param("delete_event", "event_id")
        self.service.events().delete(calendarId="primary", eventId=event_id).execute()
        return self._ok("delete_event", f"Event {event_id} deleted.")
