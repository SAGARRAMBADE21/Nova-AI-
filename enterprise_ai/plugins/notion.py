"""
plugins/notion.py
Notion Plugin — create, get, search, update pages and append blocks.

Improvements:
- update_database now makes a real API call to update a database entry.
- list_database_items action added.
- _search now extracts title from results for richer output.
- Full ActionSchema.
"""

import os
import logging
from .base import BasePlugin, PluginResult, with_retry, ActionSchema, ParamSpec

logger = logging.getLogger(__name__)


class NotionPlugin(BasePlugin):
    name = "notion"
    ACTIONS = [
        "create_page", "get_page",
        "search_pages", "update_page",
        "append_blocks", "update_database",
        "list_database_items",
    ]

    def __init__(self):
        self.client = self._init_client()

    def _init_client(self):
        try:
            from notion_client import Client
            key = os.getenv("NOTION_API_KEY", "")
            if key and key != "your_notion_api_key":
                return Client(auth=key)
        except ImportError:
            logger.warning("[Notion] notion-client not installed. Run: pip install notion-client")
        return None

    def health_check(self) -> bool:
        if not self.client:
            return False
        try:
            self.client.users.me()
            return True
        except Exception:
            return False

    # ── Schema ────────────────────────────────────────────────────────────

    def get_schema(self):
        return [
            ActionSchema("create_page", "Create a new page in a Notion workspace.", [
                ParamSpec("title",       "string", required=False, description="Page title.", default="New Page"),
                ParamSpec("database_id", "string", required=False, description="Parent database ID (if creating a DB entry)."),
                ParamSpec("page_id",     "string", required=False, description="Parent page ID (if creating a sub-page)."),
                ParamSpec("content",     "string", required=False, description="Initial paragraph text content."),
                ParamSpec("properties",  "dict",   required=False, description="Additional Notion page properties."),
            ]),
            ActionSchema("get_page", "Get metadata and title of a Notion page.", [
                ParamSpec("page_id", "string", required=True, description="Notion page ID."),
            ]),
            ActionSchema("search_pages", "Search Notion pages by query string.", [
                ParamSpec("query",     "string",  required=False, description="Search query.", default=""),
                ParamSpec("page_size", "integer", required=False, description="Max results.", default=10),
            ]),
            ActionSchema("update_page", "Update properties of a Notion page.", [
                ParamSpec("page_id",    "string", required=True,  description="Notion page ID."),
                ParamSpec("properties", "dict",   required=True,  description="Notion property dict to update."),
            ]),
            ActionSchema("append_blocks", "Append paragraph text blocks to a Notion page.", [
                ParamSpec("page_id", "string", required=True,  description="Notion page ID."),
                ParamSpec("content", "string", required=True,  description="Text content to append."),
            ]),
            ActionSchema("update_database", "Update a single entry (page) in a Notion database.", [
                ParamSpec("page_id",    "string", required=True,  description="Notion page ID of the database entry."),
                ParamSpec("properties", "dict",   required=True,  description="Properties to update on the database entry."),
            ]),
            ActionSchema("list_database_items", "List all entries in a Notion database.", [
                ParamSpec("database_id", "string",  required=True,  description="Notion database ID."),
                ParamSpec("page_size",   "integer", required=False, description="Max entries to return.", default=20),
                ParamSpec("filter",      "dict",    required=False, description="Optional Notion filter object."),
                ParamSpec("sorts",       "list",    required=False, description="Optional Notion sort list."),
            ]),
        ]

    # ── Dispatch ──────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "create_page":         self._create_page,
            "get_page":            self._get_page,
            "search_pages":        self._search,
            "update_page":         self._update_page,
            "append_blocks":       self._append_blocks,
            "update_database":     self._update_db,
            "list_database_items": self._list_db_items,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _extract_title(page: dict) -> str:
        for prop in page.get("properties", {}).values():
            if prop.get("type") == "title":
                return "".join(t.get("plain_text", "") for t in prop.get("title", []))
        return ""

    # ── Actions ───────────────────────────────────────────────────────────

    @with_retry()
    def _create_page(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("create_page")
        title = params.get("title", "New Page")
        if not (params.get("database_id") or params.get("page_id")):
            return self._missing_param("create_page", "database_id or page_id")
        parent = ({"database_id": params["database_id"]} if params.get("database_id")
                  else {"page_id": params["page_id"]})
        children = []
        if params.get("content"):
            children.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text",
                                             "text": {"content": params["content"]}}]},
            })
        # Merge user-supplied properties with the title
        properties = {"Name": {"title": [{"text": {"content": title}}]}}
        properties.update(params.get("properties") or {})
        page = self.client.pages.create(
            parent=parent,
            properties=properties,
            children=children,
        )
        return self._ok("create_page", f"Page created: {title}",
                        data={"page_id": page["id"]}, url=page.get("url"))

    @with_retry()
    def _get_page(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("get_page")
        page_id = params.get("page_id", "").strip()
        if not page_id:
            return self._missing_param("get_page", "page_id")
        page  = self.client.pages.retrieve(page_id=page_id)
        title = self._extract_title(page)
        return self._ok("get_page", f"Page: {title}",
                        data={"page_id":      page["id"],
                              "title":        title,
                              "url":          page.get("url"),
                              "created_time": page.get("created_time"),
                              "last_edited":  page.get("last_edited_time")})

    @with_retry()
    def _search(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("search_pages")
        results = self.client.search(
            query=params.get("query", ""),
            filter={"property": "object", "value": "page"},
            page_size=params.get("page_size", 10),
        )
        pages = [
            {"id":    r["id"],
             "title": self._extract_title(r),
             "url":   r.get("url")}
            for r in results.get("results", [])
        ]
        return self._ok("search_pages", f"Found {len(pages)} pages.", data=pages)

    @with_retry()
    def _update_page(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("update_page")
        page_id    = params.get("page_id", "").strip()
        properties = params.get("properties", {})
        if not page_id:
            return self._missing_param("update_page", "page_id")
        if not properties:
            return self._missing_param("update_page", "properties")
        self.client.pages.update(page_id=page_id, properties=properties)
        return self._ok("update_page", f"Page {page_id} updated.")

    @with_retry()
    def _append_blocks(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("append_blocks")
        page_id = params.get("page_id", "").strip()
        content = params.get("content", "").strip()
        if not page_id:
            return self._missing_param("append_blocks", "page_id")
        if not content:
            return self._missing_param("append_blocks", "content")
        blocks = [{
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text",
                                         "text": {"content": content}}]},
        }]
        self.client.blocks.children.append(block_id=page_id, children=blocks)
        return self._ok("append_blocks", "Content appended to page.")

    @with_retry()
    def _update_db(self, params: dict) -> PluginResult:
        """Update a Notion database entry by its page_id."""
        if not self.client:
            return self._not_connected("update_database")
        page_id    = params.get("page_id", "").strip()
        properties = params.get("properties", {})
        if not page_id:
            return self._missing_param("update_database", "page_id")
        if not properties:
            return self._missing_param("update_database", "properties")
        self.client.pages.update(page_id=page_id, properties=properties)
        return self._ok("update_database", f"Database entry {page_id} updated.")

    @with_retry()
    def _list_db_items(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("list_database_items")
        database_id = params.get("database_id", "").strip()
        if not database_id:
            return self._missing_param("list_database_items", "database_id")
        kwargs = {"database_id": database_id, "page_size": params.get("page_size", 20)}
        if params.get("filter"):
            kwargs["filter"] = params["filter"]
        if params.get("sorts"):
            kwargs["sorts"] = params["sorts"]
        results = self.client.databases.query(**kwargs)
        items = [
            {"id":    r["id"],
             "title": self._extract_title(r),
             "url":   r.get("url")}
            for r in results.get("results", [])
        ]
        return self._ok("list_database_items",
                        f"Found {len(items)} entries in database.",
                        data=items)
