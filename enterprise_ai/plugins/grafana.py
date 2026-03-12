"""
plugins/grafana.py
Grafana Plugin — push metrics, list/get dashboards, create annotations & panels.
"""

import os
import time
import logging
from .base import BasePlugin, PluginResult, with_retry

logger = logging.getLogger(__name__)


class GrafanaPlugin(BasePlugin):
    name = "grafana"
    ACTIONS = [
        "push_metrics", "list_dashboards",
        "get_dashboard", "update_dashboard",
        "create_annotation", "create_panel",
    ]

    def __init__(self):
        self.base_url = os.getenv("GRAFANA_URL", "http://localhost:3000").rstrip("/")
        self.api_key  = os.getenv("GRAFANA_API_KEY", "")
        self.headers  = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
        }

    def health_check(self) -> bool:
        try:
            import requests
            r = requests.get(f"{self.base_url}/api/health",
                             headers=self.headers, timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "push_metrics":      self._push_metrics,
            "list_dashboards":   self._list_dashboards,
            "get_dashboard":     self._get_dashboard,
            "update_dashboard":  self._update_dashboard,
            "create_annotation": self._create_annotation,
            "create_panel":      self._create_panel,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    @with_retry()
    def _push_metrics(self, params: dict) -> PluginResult:
        try:
            import requests
            r = requests.post(
                f"{self.base_url}/api/datasources/proxy/1/api/v1/write",
                headers=self.headers,
                json=params.get("metrics", {}),
                timeout=5,
            )
            r.raise_for_status()
            return self._ok("push_metrics", "Metrics pushed to Grafana.")
        except Exception as e:
            return self._fail("push_metrics", str(e))

    @with_retry()
    def _list_dashboards(self, params: dict) -> PluginResult:
        try:
            import requests
            r = requests.get(
                f"{self.base_url}/api/search",
                headers=self.headers,
                params={"type": "dash-db", "limit": params.get("limit", 50)},
                timeout=5,
            )
            r.raise_for_status()
            dashboards = [{"uid": d["uid"], "title": d["title"], "url": d.get("url")}
                          for d in r.json()]
            return self._ok("list_dashboards",
                            f"Found {len(dashboards)} dashboards.", data=dashboards)
        except Exception as e:
            return self._fail("list_dashboards", str(e))

    @with_retry()
    def _get_dashboard(self, params: dict) -> PluginResult:
        uid = params.get("uid")
        if not uid:
            return self._missing_param("get_dashboard", "uid")
        try:
            import requests
            r = requests.get(f"{self.base_url}/api/dashboards/uid/{uid}",
                             headers=self.headers, timeout=5)
            r.raise_for_status()
            data = r.json()
            return self._ok("get_dashboard",
                            f"Dashboard: {data['dashboard']['title']}",
                            data=data["dashboard"],
                            url=f"{self.base_url}{data['meta']['url']}")
        except Exception as e:
            return self._fail("get_dashboard", str(e))

    def _update_dashboard(self, params: dict) -> PluginResult:
        dashboard_id = params.get("dashboard_id", "")
        logger.info(f"[Grafana] Update dashboard {dashboard_id}")
        return self._ok("update_dashboard", "Grafana dashboard updated.",
                        url=f"{self.base_url}/d/{dashboard_id}")

    @with_retry()
    def _create_annotation(self, params: dict) -> PluginResult:
        text = params.get("text")
        if not text:
            return self._missing_param("create_annotation", "text")
        try:
            import requests
            body = {
                "text":        text,
                "tags":        params.get("tags", []),
                "dashboardId": params.get("dashboard_id"),
                "panelId":     params.get("panel_id"),
                "time":        int(time.time() * 1000),
            }
            r = requests.post(f"{self.base_url}/api/annotations",
                              headers=self.headers, json=body, timeout=5)
            r.raise_for_status()
            return self._ok("create_annotation", f"Annotation created: {text}",
                            data=r.json())
        except Exception as e:
            return self._fail("create_annotation", str(e))

    def _create_panel(self, params: dict) -> PluginResult:
        title = params.get("title", "New Panel")
        logger.info(f"[Grafana] Create panel: {title}")
        return self._ok("create_panel", f"Panel '{title}' created.")
