"""
plugins/google_drive.py
Google Drive Plugin — list, search, upload, download, delete, share files.
"""

import os
import logging
from .base import BasePlugin, PluginResult, with_retry

logger = logging.getLogger(__name__)


class GoogleDrivePlugin(BasePlugin):
    name = "google_drive"
    ACTIONS = [
        "list_files", "search_files", "upload_file",
        "download_file", "delete_file", "share_file",
    ]

    def __init__(self):
        self.service = self._init_service()

    def _init_service(self):
        try:
            from googleapiclient.discovery import build
            creds = self._google_creds()
            if creds:
                return build("drive", "v3", credentials=creds)
        except Exception as e:
            logger.warning(f"[GoogleDrive] Init failed: {e}")
        return None

    def health_check(self) -> bool:
        if not self.service:
            return False
        try:
            self.service.files().list(pageSize=1).execute()
            return True
        except Exception:
            return False

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "list_files":    self._list_files,
            "search_files":  self._search_files,
            "upload_file":   self._upload_file,
            "download_file": self._download_file,
            "delete_file":   self._delete_file,
            "share_file":    self._share_file,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    @with_retry()
    def _list_files(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("list_files")
        page_size = params.get("page_size", 20)
        results = self.service.files().list(
            pageSize=page_size,
            fields="files(id, name, mimeType, webViewLink, modifiedTime)",
        ).execute()
        files = results.get("files", [])
        return self._ok("list_files", f"Found {len(files)} files.", data=files)

    @with_retry()
    def _search_files(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("search_files")
        query = params.get("query")
        if not query:
            return self._missing_param("search_files", "query")
        results = self.service.files().list(
            q=f"name contains '{query}'",
            fields="files(id, name, mimeType, webViewLink, modifiedTime)",
        ).execute()
        files = results.get("files", [])
        return self._ok("search_files", f"Found {len(files)} matching files.", data=files)

    @with_retry()
    def _upload_file(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("upload_file")
        name = params.get("name")
        if not name:
            return self._missing_param("upload_file", "name")
        from googleapiclient.http import MediaInMemoryUpload
        data  = (params.get("content") or "").encode()
        media = MediaInMemoryUpload(data, mimetype=params.get("mimetype", "text/plain"))
        parents = [params["folder_id"]] if params.get("folder_id") else []
        file = self.service.files().create(
            body={"name": name, "parents": parents},
            media_body=media,
            fields="id,webViewLink",
        ).execute()
        return self._ok("upload_file", f"Uploaded: {name}",
                        data={"file_id": file["id"]}, url=file.get("webViewLink"))

    @with_retry()
    def _download_file(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("download_file")
        file_id = params.get("file_id")
        if not file_id:
            return self._missing_param("download_file", "file_id")
        content = self.service.files().get_media(fileId=file_id).execute()
        return self._ok("download_file", "File downloaded.",
                        data={"content": content.decode(errors="replace")})

    @with_retry()
    def _delete_file(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("delete_file")
        file_id = params.get("file_id")
        if not file_id:
            return self._missing_param("delete_file", "file_id")
        self.service.files().delete(fileId=file_id).execute()
        return self._ok("delete_file", f"File {file_id} deleted.")

    @with_retry()
    def _share_file(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("share_file")
        file_id = params.get("file_id")
        email   = params.get("email")
        role    = params.get("role", "reader")
        if not file_id:
            return self._missing_param("share_file", "file_id")
        if not email:
            return self._missing_param("share_file", "email")
        self.service.permissions().create(
            fileId=file_id,
            body={"type": "user", "role": role, "emailAddress": email},
            sendNotificationEmail=params.get("notify", True),
        ).execute()
        return self._ok("share_file", f"File shared with {email} as {role}.")
