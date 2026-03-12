"""
plugins/plugin_system.py
Backward-compatibility shim.
All plugin classes now live in their own individual files.
Import from here or directly from the individual modules.
"""

from .base            import BasePlugin, PluginResult, with_retry
from .google_drive    import GoogleDrivePlugin
from .google_docs     import GoogleDocsPlugin
from .google_sheets   import GoogleSheetsPlugin
from .google_calendar import GoogleCalendarPlugin
from .gmail           import GmailPlugin
from .google_meet     import GoogleMeetPlugin
from .slack           import SlackPlugin
from .notion          import NotionPlugin
from .grafana         import GrafanaPlugin
from .registry        import PluginRegistry

__all__ = [
    "BasePlugin", "PluginResult", "with_retry",
    "GoogleDrivePlugin", "GoogleDocsPlugin", "GoogleSheetsPlugin",
    "GoogleCalendarPlugin", "GmailPlugin", "GoogleMeetPlugin",
    "SlackPlugin", "NotionPlugin", "GrafanaPlugin",
    "PluginRegistry",
]
