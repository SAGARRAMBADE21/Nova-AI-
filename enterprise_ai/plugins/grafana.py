"""
plugins/grafana.py
Grafana Plugin — push metrics, list/get dashboards, create annotations & panels.

Improvements:
- update_dashboard now performs a real API call (was a stub).
- create_panel now performs a real API call (was a stub).
- delete_dashboard action added.
- query_datasource action added for ad-hoc metric queries.
- Shared _request helper to avoid repetitive try/except/import blocks.
- Full ActionSchema.
"""

import os
import time
import logging
import requests
from .base import BasePlugin, PluginResult, with_retry, ActionSchema, ParamSpec

logger = logging.getLogger(__name__)


class GrafanaPlugin(BasePlugin):
    name = "grafana"
    ACTIONS = [
        "push_metrics", "list_dashboards",
        "get_dashboard", "update_dashboard",
        "create_annotation", "create_panel",
        "delete_dashboard", "query_datasource",
    ]

    def __init__(self):
        self.base_url = os.getenv("GRAFANA_URL", "http://localhost:3000").rstrip("/")
        api_key       = os.getenv("GRAFANA_API_KEY", "")
        sa_token      = os.getenv("GRAFANA_SERVICE_ACCOUNT_TOKEN", "")
        # Prefer Service Account token (modern), fall back to API key
        token         = sa_token or api_key
        self.headers  = {
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        }

    def health_check(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/health",
                             headers=self.headers, timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    # ── Schema ────────────────────────────────────────────────────────────

    def get_schema(self):
        return [
            ActionSchema("push_metrics", "Push raw metrics to a Grafana datasource proxy.", [
                ParamSpec("metrics",       "dict",    required=True,  description="Metrics payload dict."),
                ParamSpec("datasource_id", "integer", required=False, description="Datasource proxy ID.", default=1),
            ]),
            ActionSchema("list_dashboards", "List all dashboards in Grafana.", [
                ParamSpec("limit", "integer", required=False, description="Max dashboards to return.", default=50),
                ParamSpec("query", "string",  required=False, description="Filter dashboards by title substring."),
            ]),
            ActionSchema("get_dashboard", "Get a Grafana dashboard by its UID.", [
                ParamSpec("uid", "string", required=True, description="Grafana dashboard UID."),
            ]),
            ActionSchema("update_dashboard", "Update an existing Grafana dashboard.", [
                ParamSpec("uid",       "string", required=True,  description="Dashboard UID."),
                ParamSpec("title",     "string", required=False, description="New title for the dashboard."),
                ParamSpec("overwrite", "boolean", required=False, description="Overwrite if exists.", default=True),
            ]),
            ActionSchema("delete_dashboard", "Delete a Grafana dashboard by UID.", [
                ParamSpec("uid", "string", required=True, description="Grafana dashboard UID."),
            ]),
            ActionSchema("create_annotation", "Create an annotation on a Grafana dashboard.", [
                ParamSpec("text",         "string", required=True,  description="Annotation text."),
                ParamSpec("tags",         "list",   required=False, description="List of tag strings.", default=[]),
                ParamSpec("dashboard_id", "integer", required=False, description="Target dashboard ID."),
                ParamSpec("panel_id",     "integer", required=False, description="Target panel ID."),
            ]),
            ActionSchema("create_panel", "Add a new graph panel to an existing Grafana dashboard.", [
                ParamSpec("uid",    "string", required=True,  description="Dashboard UID to add panel to."),
                ParamSpec("title",  "string", required=False, description="Panel title.", default="New Panel"),
                ParamSpec("target", "string", required=False, description="PromQL or datasource query."),
            ]),
            ActionSchema("query_datasource", "Run an instant query against a Grafana datasource.", [
                ParamSpec("datasource_uid", "string", required=True,  description="Datasource UID."),
                ParamSpec("expr",           "string", required=True,  description="Query expression (e.g. PromQL)."),
                ParamSpec("start",          "string", required=False, description="Unix timestamp or relative time (e.g. 'now-1h')."),
                ParamSpec("end",            "string", required=False, description="Unix timestamp or 'now'."),
                ParamSpec("step",           "string", required=False, description="Step interval, e.g. '60s'.", default="60s"),
            ]),
        ]

    # ── Dispatch ──────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "push_metrics":      self._push_metrics,
            "list_dashboards":   self._list_dashboards,
            "get_dashboard":     self._get_dashboard,
            "update_dashboard":  self._update_dashboard,
            "delete_dashboard":  self._delete_dashboard,
            "create_annotation": self._create_annotation,
            "create_panel":      self._create_panel,
            "query_datasource":  self._query_datasource,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    # ── Shared request helper ─────────────────────────────────────────────

    def _req(self, method: str, path: str, **kwargs):
        """Wrapper around requests that always applies base_url and headers."""
        url = f"{self.base_url}{path}"
        kwargs.setdefault("headers", self.headers)
        kwargs.setdefault("timeout", 10)
        r = requests.request(method, url, **kwargs)
        r.raise_for_status()
        return r

    # ── Actions ───────────────────────────────────────────────────────────

    @with_retry()
    def _push_metrics(self, params: dict) -> PluginResult:
        metrics = params.get("metrics")
        if not metrics:
            return self._missing_param("push_metrics", "metrics")
        datasource_id = params.get("datasource_id", 1)
        try:
            self._req("POST",
                      f"/api/datasources/proxy/{datasource_id}/api/v1/write",
                      json=metrics)
            return self._ok("push_metrics", "Metrics pushed to Grafana.")
        except Exception as e:
            return self._fail("push_metrics", str(e))

    @with_retry()
    def _list_dashboards(self, params: dict) -> PluginResult:
        try:
            query_params = {"type": "dash-db", "limit": params.get("limit", 50)}
            if params.get("query"):
                query_params["query"] = params["query"]
            r = self._req("GET", "/api/search", params=query_params)
            dashboards = [{"uid": d["uid"], "title": d["title"],
                           "url": f"{self.base_url}{d.get('url', '')}"}
                          for d in r.json()]
            return self._ok("list_dashboards",
                            f"Found {len(dashboards)} dashboards.", data=dashboards)
        except Exception as e:
            return self._fail("list_dashboards", str(e))

    @with_retry()
    def _get_dashboard(self, params: dict) -> PluginResult:
        uid = params.get("uid", "").strip()
        if not uid:
            return self._missing_param("get_dashboard", "uid")
        try:
            r    = self._req("GET", f"/api/dashboards/uid/{uid}")
            data = r.json()
            return self._ok("get_dashboard",
                            f"Dashboard: {data['dashboard']['title']}",
                            data=data["dashboard"],
                            url=f"{self.base_url}{data['meta']['url']}")
        except Exception as e:
            return self._fail("get_dashboard", str(e))

    @with_retry()
    def _update_dashboard(self, params: dict) -> PluginResult:
        uid = params.get("uid", "").strip()
        if not uid:
            return self._missing_param("update_dashboard", "uid")
        try:
            # Fetch the existing dashboard first
            r        = self._req("GET", f"/api/dashboards/uid/{uid}")
            envelope = r.json()
            dashboard = envelope["dashboard"]
            folder_id = envelope.get("meta", {}).get("folderId", 0)
            if params.get("title"):
                dashboard["title"] = params["title"]
            # Bump version for the update
            payload = {
                "dashboard": dashboard,
                "folderId":  folder_id,
                "overwrite": params.get("overwrite", True),
                "message":   "Updated via Nova AI",
            }
            r2 = self._req("POST", "/api/dashboards/db", json=payload)
            resp = r2.json()
            return self._ok("update_dashboard",
                            f"Dashboard '{dashboard['title']}' updated.",
                            url=f"{self.base_url}{resp.get('url', '')}")
        except Exception as e:
            return self._fail("update_dashboard", str(e))

    @with_retry()
    def _delete_dashboard(self, params: dict) -> PluginResult:
        uid = params.get("uid", "").strip()
        if not uid:
            return self._missing_param("delete_dashboard", "uid")
        try:
            self._req("DELETE", f"/api/dashboards/uid/{uid}")
            return self._ok("delete_dashboard", f"Dashboard {uid} deleted.")
        except Exception as e:
            return self._fail("delete_dashboard", str(e))

    @with_retry()
    def _create_annotation(self, params: dict) -> PluginResult:
        text = params.get("text", "").strip()
        if not text:
            return self._missing_param("create_annotation", "text")
        try:
            body = {
                "text":        text,
                "tags":        params.get("tags", []),
                "dashboardId": params.get("dashboard_id"),
                "panelId":     params.get("panel_id"),
                "time":        int(time.time() * 1000),
            }
            r = self._req("POST", "/api/annotations", json=body)
            return self._ok("create_annotation", f"Annotation created: {text}",
                            data=r.json())
        except Exception as e:
            return self._fail("create_annotation", str(e))

    @with_retry()
    def _create_panel(self, params: dict) -> PluginResult:
        uid   = params.get("uid", "").strip()
        title = params.get("title", "New Panel").strip()
        if not uid:
            return self._missing_param("create_panel", "uid")
        try:
            r         = self._req("GET", f"/api/dashboards/uid/{uid}")
            envelope  = r.json()
            dashboard = envelope["dashboard"]
            folder_id = envelope.get("meta", {}).get("folderId", 0)
            panels    = dashboard.get("panels", [])
            next_id   = max((p.get("id", 0) for p in panels), default=0) + 1
            new_panel = {
                "id":         next_id,
                "type":       "graph",
                "title":      title,
                "gridPos":    {"x": 0, "y": len(panels) * 8, "w": 24, "h": 8},
                "datasource": None,
                "targets":    [],
            }
            if params.get("target"):
                new_panel["targets"].append({"expr": params["target"], "refId": "A"})
            panels.append(new_panel)
            dashboard["panels"] = panels
            payload = {
                "dashboard": dashboard,
                "folderId":  folder_id,
                "overwrite": True,
                "message":   f"Added panel '{title}' via Nova AI",
            }
            r2 = self._req("POST", "/api/dashboards/db", json=payload)
            resp = r2.json()
            return self._ok("create_panel", f"Panel '{title}' added to dashboard {uid}.",
                            url=f"{self.base_url}{resp.get('url', '')}")
        except Exception as e:
            return self._fail("create_panel", str(e))

    @with_retry()
    def _query_datasource(self, params: dict) -> PluginResult:
        ds_uid = params.get("datasource_uid", "").strip()
        expr   = params.get("expr", "").strip()
        if not ds_uid:
            return self._missing_param("query_datasource", "datasource_uid")
        if not expr:
            return self._missing_param("query_datasource", "expr")
        try:
            body = {
                "queries": [{
                    "refId":         "A",
                    "datasource":    {"uid": ds_uid},
                    "expr":          expr,
                    "step":          params.get("step", "60s"),
                    "instant":       True,
                }],
                "from": params.get("start", "now-1h"),
                "to":   params.get("end",   "now"),
            }
            r = self._req("POST", "/api/ds/query", json=body)
            return self._ok("query_datasource", f"Query executed on datasource {ds_uid}.",
                            data=r.json())
        except Exception as e:
            return self._fail("query_datasource", str(e))
