# plugins/__init__.py
# Convenience imports — everything accessible from `plugins` package directly.

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
