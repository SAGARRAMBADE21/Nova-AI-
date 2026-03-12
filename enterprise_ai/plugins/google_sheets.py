"""
plugins/google_sheets.py
Google Sheets Plugin — create, read, push, append, clear spreadsheets.
"""

import logging
from .base import BasePlugin, PluginResult, with_retry

logger = logging.getLogger(__name__)


class GoogleSheetsPlugin(BasePlugin):
    name = "google_sheets"
    ACTIONS = [
        "create_spreadsheet", "read_data",
        "push_data", "append_row", "clear_range",
    ]

    def __init__(self):
        self.service = self._init_service()

    def _init_service(self):
        try:
            from googleapiclient.discovery import build
            creds = self._google_creds()
            if creds:
                return build("sheets", "v4", credentials=creds)
        except Exception as e:
            logger.warning(f"[GoogleSheets] Init failed: {e}")
        return None

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "create_spreadsheet": self._create,
            "read_data":          self._read,
            "push_data":          self._push,
            "append_row":         self._append_row,
            "clear_range":        self._clear,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    @with_retry()
    def _create(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("create_spreadsheet")
        title = params.get("title", "New Spreadsheet")
        sheet = self.service.spreadsheets().create(
            body={"properties": {"title": title}}
        ).execute()
        sid = sheet["spreadsheetId"]
        url = f"https://docs.google.com/spreadsheets/d/{sid}/edit"
        return self._ok("create_spreadsheet", f"Created: {title}",
                        data={"spreadsheet_id": sid}, url=url)

    @with_retry()
    def _read(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("read_data")
        sid   = params.get("spreadsheet_id")
        range_ = params.get("range", "Sheet1!A1:Z100")
        if not sid:
            return self._missing_param("read_data", "spreadsheet_id")
        result = self.service.spreadsheets().values().get(
            spreadsheetId=sid, range=range_
        ).execute()
        rows = result.get("values", [])
        return self._ok("read_data", f"Read {len(rows)} rows.", data={"rows": rows})

    @with_retry()
    def _push(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("push_data")
        sid    = params.get("spreadsheet_id")
        range_ = params.get("range", "Sheet1!A1")
        values = params.get("values", [])
        if not sid:
            return self._missing_param("push_data", "spreadsheet_id")
        self.service.spreadsheets().values().update(
            spreadsheetId=sid, range=range_,
            valueInputOption="USER_ENTERED",
            body={"values": values},
        ).execute()
        return self._ok("push_data", f"Data written to {range_}.")

    @with_retry()
    def _append_row(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("append_row")
        sid    = params.get("spreadsheet_id")
        range_ = params.get("range", "Sheet1")
        values = params.get("values", [])
        if not sid:
            return self._missing_param("append_row", "spreadsheet_id")
        self.service.spreadsheets().values().append(
            spreadsheetId=sid, range=range_,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [values]},
        ).execute()
        return self._ok("append_row", f"Row appended to {range_}.")

    @with_retry()
    def _clear(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("clear_range")
        sid    = params.get("spreadsheet_id")
        range_ = params.get("range", "Sheet1")
        if not sid:
            return self._missing_param("clear_range", "spreadsheet_id")
        self.service.spreadsheets().values().clear(
            spreadsheetId=sid, range=range_, body={}
        ).execute()
        return self._ok("clear_range", f"Range {range_} cleared.")
