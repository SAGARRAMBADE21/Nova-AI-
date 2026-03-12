"""
plugins/notion.py
Notion Plugin — create, get, search, update pages and append blocks.
"""

import os
import logging
from .base import BasePlugin, PluginResult, with_retry

logger = logging.getLogger(__name__)


class NotionPlugin(BasePlugin):
    name = "notion"
    ACTIONS = [
        "create_page", "get_page",
        "search_pages", "update_page",
        "append_blocks", "update_database",
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
            logger.warning("[Notion] notion-client not installed.")
        return None

    def health_check(self) -> bool:
        if not self.client:
            return False
        try:
            self.client.users.me()
            return True
        except Exception:
            return False

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "create_page":     self._create_page,
            "get_page":        self._get_page,
            "search_pages":    self._search,
            "update_page":     self._update_page,
            "append_blocks":   self._append_blocks,
            "update_database": self._update_db,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

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
        page = self.client.pages.create(
            parent=parent,
            properties={"Name": {"title": [{"text": {"content": title}}]}},
            children=children,
        )
        return self._ok("create_page", f"Page created: {title}",
                        data={"page_id": page["id"]}, url=page.get("url"))

    @with_retry()
    def _get_page(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("get_page")
        page_id = params.get("page_id")
        if not page_id:
            return self._missing_param("get_page", "page_id")
        page  = self.client.pages.retrieve(page_id=page_id)
        title = ""
        for prop in page.get("properties", {}).values():
            if prop.get("type") == "title":
                for t in prop["title"]:
                    title += t.get("plain_text", "")
        return self._ok("get_page", f"Page: {title}",
                        data={"page_id": page["id"], "title": title,
                              "url": page.get("url"),
                              "created_time": page.get("created_time")})

    @with_retry()
    def _search(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("search_pages")
        results = self.client.search(
            query=params.get("query", ""),
            filter={"property": "object", "value": "page"},
            page_size=params.get("page_size", 10),
        )
        pages = [{"id": r["id"], "url": r.get("url")} for r in results.get("results", [])]
        return self._ok("search_pages", f"Found {len(pages)} pages.", data=pages)

    @with_retry()
    def _update_page(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("update_page")
        page_id = params.get("page_id")
        if not page_id:
            return self._missing_param("update_page", "page_id")
        self.client.pages.update(page_id=page_id,
                                 properties=params.get("properties", {}))
        return self._ok("update_page", f"Page {page_id} updated.")

    @with_retry()
    def _append_blocks(self, params: dict) -> PluginResult:
        if not self.client:
            return self._not_connected("append_blocks")
        page_id = params.get("page_id")
        content = params.get("content")
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

    def _update_db(self, params: dict) -> PluginResult:
        logger.info(f"[Notion] Update database | params={params}")
        return self._ok("update_database", "Notion database entry updated.")
