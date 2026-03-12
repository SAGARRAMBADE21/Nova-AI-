"""
plugins/registry.py
PluginRegistry — central registry for all plugins.
Supports: execute, list_plugins, list_actions, health_report.
"""

import logging
from typing import Optional, List
from .base import BasePlugin, PluginResult
from .google_drive    import GoogleDrivePlugin
from .google_docs     import GoogleDocsPlugin
from .google_sheets   import GoogleSheetsPlugin
from .google_calendar import GoogleCalendarPlugin
from .gmail           import GmailPlugin
from .google_meet     import GoogleMeetPlugin
from .slack           import SlackPlugin
from .notion          import NotionPlugin
from .grafana         import GrafanaPlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central plugin registry.
    - execute(plugin, action, params) — main entry point
    - list_plugins()                  — discover all plugin names
    - list_actions(plugin)            — discover actions per plugin
    - health_report()                 — connectivity status of all plugins
    """

    def __init__(self):
        self._plugins: dict[str, BasePlugin] = {}
        self._register_all()

    def _register_all(self):
        plugins = [
            GoogleDrivePlugin(),
            GoogleDocsPlugin(),
            GoogleSheetsPlugin(),
            GoogleCalendarPlugin(),
            GmailPlugin(),
            GoogleMeetPlugin(),
            SlackPlugin(),
            NotionPlugin(),
            GrafanaPlugin(),
        ]
        for plugin in plugins:
            self._plugins[plugin.name] = plugin
            logger.info(f"[PluginRegistry] Registered: {plugin.name}")

    def get(self, name: str) -> Optional[BasePlugin]:
        return self._plugins.get(name)

    def list_plugins(self) -> List[str]:
        """Return names of all registered plugins."""
        return list(self._plugins.keys())

    def list_actions(self, plugin_name: str) -> List[str]:
        """Return supported actions for a plugin."""
        plugin = self.get(plugin_name)
        return plugin.list_actions() if plugin else []

    def health_report(self) -> dict:
        """Run health checks across all plugins."""
        report = {}
        for name, plugin in self._plugins.items():
            try:
                report[name] = "healthy" if plugin.health_check() else "unavailable"
            except Exception as e:
                report[name] = f"error: {e}"
        logger.info(f"[PluginRegistry] Health report: {report}")
        return report

    def execute(self, plugin_name: str, action: str, params: dict) -> PluginResult:
        plugin = self.get(plugin_name)
        if not plugin:
            logger.error(f"[PluginRegistry] Plugin '{plugin_name}' not found.")
            return PluginResult(
                plugin_name, action, False,
                f"Plugin '{plugin_name}' not found. "
                f"Available: {', '.join(self.list_plugins())}",
                error_code="PLUGIN_NOT_FOUND",
            )
        logger.info(f"[PluginRegistry] → {plugin_name}.{action}()")
        try:
            return plugin.execute(action, params)
        except Exception as e:
            logger.exception(f"[PluginRegistry] Unhandled error in {plugin_name}.{action}: {e}")
            return PluginResult(plugin_name, action, False,
                                f"Unexpected error: {e}",
                                error_code="INTERNAL_ERROR")
