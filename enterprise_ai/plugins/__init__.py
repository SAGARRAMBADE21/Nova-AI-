# plugins/__init__.py
# Convenience imports — everything accessible from `plugins` package directly.

from .base            import BasePlugin, PluginResult, ActionSchema, ParamSpec, with_retry
from .google_drive    import GoogleDrivePlugin
from .google_docs     import GoogleDocsPlugin
from .google_sheets   import GoogleSheetsPlugin
from .google_calendar import GoogleCalendarPlugin
from .gmail           import GmailPlugin
from .google_meet     import GoogleMeetPlugin
from .grafana         import GrafanaPlugin
from .registry        import PluginRegistry

__all__ = [
    # Base
    "BasePlugin", "PluginResult", "ActionSchema", "ParamSpec", "with_retry",
    # Google
    "GoogleDrivePlugin", "GoogleDocsPlugin", "GoogleSheetsPlugin",
    "GoogleCalendarPlugin", "GmailPlugin", "GoogleMeetPlugin",
    # Dashboard
    "GrafanaPlugin",
    # Registry
    "PluginRegistry",
]
