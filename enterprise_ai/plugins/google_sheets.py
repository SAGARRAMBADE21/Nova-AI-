"""
plugins/google_sheets.py
Google Sheets Plugin — create, read, push, append, clear, format spreadsheets.

Improvements:
- validate 'values' is a list in push_data / append_row.
- get_spreadsheet_info action added.
- batch_append action for multi-row appends.
- Full ActionSchema.
"""

import logging
from .base import BasePlugin, PluginResult, with_retry, ActionSchema, ParamSpec

logger = logging.getLogger(__name__)


class GoogleSheetsPlugin(BasePlugin):
    name = "google_sheets"
    ACTIONS = [
        "create_spreadsheet", "read_data",
        "push_data", "append_row",
        "clear_range", "get_spreadsheet_info",
        "batch_append",
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

    def health_check(self) -> bool:
        return bool(self.service)

    # ── Schema ────────────────────────────────────────────────────────────

    def get_schema(self):
        return [
            ActionSchema("create_spreadsheet", "Create a new Google Sheets spreadsheet.", [
                ParamSpec("title", "string", required=False, description="Spreadsheet title.", default="New Spreadsheet"),
            ]),
            ActionSchema("read_data", "Read values from a spreadsheet range.", [
                ParamSpec("spreadsheet_id", "string", required=True,  description="Google Sheets spreadsheet ID."),
                ParamSpec("range",          "string", required=False, description="A1 notation range, e.g. 'Sheet1!A1:Z100'.", default="Sheet1!A1:Z100"),
            ]),
            ActionSchema("push_data", "Write values to a spreadsheet range (overwrites).", [
                ParamSpec("spreadsheet_id", "string", required=True,  description="Google Sheets spreadsheet ID."),
                ParamSpec("range",          "string", required=False, description="A1 notation range.", default="Sheet1!A1"),
                ParamSpec("values",         "list",   required=True,  description="2D list of values, e.g. [['Name','Age'],['Alice',30]]."),
            ]),
            ActionSchema("append_row", "Append a single row to a spreadsheet.", [
                ParamSpec("spreadsheet_id", "string", required=True,  description="Google Sheets spreadsheet ID."),
                ParamSpec("range",          "string", required=False, description="Sheet to append to.", default="Sheet1"),
                ParamSpec("values",         "list",   required=True,  description="A flat list representing one row, e.g. ['Alice', 30, 'Engineering']."),
            ]),
            ActionSchema("batch_append", "Append multiple rows to a spreadsheet in a single call.", [
                ParamSpec("spreadsheet_id", "string", required=True,  description="Google Sheets spreadsheet ID."),
                ParamSpec("range",          "string", required=False, description="Sheet to append to.", default="Sheet1"),
                ParamSpec("rows",           "list",   required=True,  description="List of rows; each row is a list of values."),
            ]),
            ActionSchema("clear_range", "Clear all values in a spreadsheet range.", [
                ParamSpec("spreadsheet_id", "string", required=True,  description="Google Sheets spreadsheet ID."),
                ParamSpec("range",          "string", required=False, description="A1 notation range to clear.", default="Sheet1"),
            ]),
            ActionSchema("get_spreadsheet_info", "Get metadata about a spreadsheet (title, sheets list).", [
                ParamSpec("spreadsheet_id", "string", required=True, description="Google Sheets spreadsheet ID."),
            ]),
        ]

    # ── Dispatch ──────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "create_spreadsheet":  self._create,
            "read_data":           self._read,
            "push_data":           self._push,
            "append_row":          self._append_row,
            "batch_append":        self._batch_append,
            "clear_range":         self._clear,
            "get_spreadsheet_info":self._get_info,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    # ── Actions ───────────────────────────────────────────────────────────

    @with_retry()
    def _create(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("create_spreadsheet")
        title = params.get("title", "New Spreadsheet").strip() or "New Spreadsheet"
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
        sid   = params.get("spreadsheet_id", "").strip()
        range_ = params.get("range", "Sheet1!A1:Z100")
        if not sid:
            return self._missing_param("read_data", "spreadsheet_id")
        result = self.service.spreadsheets().values().get(
            spreadsheetId=sid, range=range_
        ).execute()
        rows = result.get("values", [])
        return self._ok("read_data", f"Read {len(rows)} rows from {range_}.",
                        data={"rows": rows, "range": result.get("range"),
                              "total_rows": len(rows)})

    @with_retry()
    def _push(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("push_data")
        sid    = params.get("spreadsheet_id", "").strip()
        range_ = params.get("range", "Sheet1!A1")
        values = params.get("values", [])
        if not sid:
            return self._missing_param("push_data", "spreadsheet_id")
        if not isinstance(values, list):
            return self._fail("push_data",
                              "'values' must be a 2D list, e.g. [['Name','Age'],['Alice',30]]",
                              error_code="INVALID_PARAMS")
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
        sid    = params.get("spreadsheet_id", "").strip()
        range_ = params.get("range", "Sheet1")
        values = params.get("values", [])
        if not sid:
            return self._missing_param("append_row", "spreadsheet_id")
        if not isinstance(values, list):
            return self._fail("append_row",
                              "'values' must be a flat list representing one row.",
                              error_code="INVALID_PARAMS")
        self.service.spreadsheets().values().append(
            spreadsheetId=sid, range=range_,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [values]},
        ).execute()
        return self._ok("append_row", f"Row appended to {range_}.")

    @with_retry()
    def _batch_append(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("batch_append")
        sid   = params.get("spreadsheet_id", "").strip()
        range_ = params.get("range", "Sheet1")
        rows   = params.get("rows", [])
        if not sid:
            return self._missing_param("batch_append", "spreadsheet_id")
        if not isinstance(rows, list) or not rows:
            return self._fail("batch_append",
                              "'rows' must be a non-empty list of lists.",
                              error_code="INVALID_PARAMS")
        self.service.spreadsheets().values().append(
            spreadsheetId=sid, range=range_,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        ).execute()
        return self._ok("batch_append", f"Appended {len(rows)} rows to {range_}.")

    @with_retry()
    def _clear(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("clear_range")
        sid    = params.get("spreadsheet_id", "").strip()
        range_ = params.get("range", "Sheet1")
        if not sid:
            return self._missing_param("clear_range", "spreadsheet_id")
        self.service.spreadsheets().values().clear(
            spreadsheetId=sid, range=range_, body={}
        ).execute()
        return self._ok("clear_range", f"Range {range_} cleared.")

    @with_retry()
    def _get_info(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("get_spreadsheet_info")
        sid = params.get("spreadsheet_id", "").strip()
        if not sid:
            return self._missing_param("get_spreadsheet_info", "spreadsheet_id")
        sheet = self.service.spreadsheets().get(
            spreadsheetId=sid,
            fields="spreadsheetId,properties,sheets.properties"
        ).execute()
        sheets = [
            {"title": s["properties"]["title"],
             "index": s["properties"]["index"],
             "row_count": s["properties"].get("gridProperties", {}).get("rowCount"),
             "column_count": s["properties"].get("gridProperties", {}).get("columnCount")}
            for s in sheet.get("sheets", [])
        ]
        return self._ok("get_spreadsheet_info",
                        f"Spreadsheet: {sheet['properties']['title']}",
                        data={"spreadsheet_id": sid,
                              "title": sheet["properties"]["title"],
                              "sheets": sheets},
                        url=f"https://docs.google.com/spreadsheets/d/{sid}/edit")
