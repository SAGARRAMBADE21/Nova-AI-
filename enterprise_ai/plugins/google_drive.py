"""
plugins/google_drive.py
Google Drive Plugin — list, search, upload, download, delete, share files.

Improvements:
- Query sanitization in search_files (prevents injection via q param).
- move_file action added.
- get_file_metadata action added.
- share_file validates role choices and email format.
- Full ActionSchema.
"""

import os
import logging
from .base import BasePlugin, PluginResult, with_retry, ActionSchema, ParamSpec

logger = logging.getLogger(__name__)

_ALLOWED_ROLES = ("reader", "commenter", "writer", "fileOrganizer", "organizer", "owner")


class GoogleDrivePlugin(BasePlugin):
    name = "google_drive"
    ACTIONS = [
        "list_files", "search_files", "upload_file",
        "download_file", "delete_file", "share_file",
        "get_file_metadata", "move_file",
    ]

    def __init__(self):
        self._service = None

    def _ensure_service(self):
        """Lazy-init / re-init the Drive service with fresh credentials."""
        if not self._service:
            self._service = self._build_google_service("drive", "v3")
        return self._service

    @property
    def service(self):
        return self._ensure_service()

    def health_check(self) -> bool:
        svc = self._ensure_service()
        if not svc:
            return False
        try:
            svc.files().list(pageSize=1).execute()
            return True
        except Exception:
            self._service = None  # force re-init on next call
            return False

    # ── Schema ────────────────────────────────────────────────────────────

    def get_schema(self):
        return [
            ActionSchema("list_files", "List files in Google Drive.", [
                ParamSpec("page_size", "integer", required=False, description="Max files to return.", default=20),
                ParamSpec("folder_id", "string",  required=False, description="Limit listing to a specific folder ID."),
            ]),
            ActionSchema("search_files", "Search for files by name or MIME type.", [
                ParamSpec("query",     "string",  required=True,  description="Search term (matched against file name)."),
                ParamSpec("mime_type", "string",  required=False, description="Optional MIME type filter, e.g. 'application/pdf'."),
                ParamSpec("folder_id", "string",  required=False, description="Limit search to a specific folder ID."),
            ]),
            ActionSchema("upload_file", "Upload a file to Google Drive.", [
                ParamSpec("name",      "string", required=True,  description="File name to create in Drive."),
                ParamSpec("content",   "string", required=False, description="Text content to upload."),
                ParamSpec("mimetype",  "string", required=False, description="MIME type.", default="text/plain"),
                ParamSpec("folder_id", "string", required=False, description="Parent folder ID."),
            ]),
            ActionSchema("download_file", "Download a file's text content from Drive.", [
                ParamSpec("file_id", "string", required=True, description="Google Drive file ID."),
            ]),
            ActionSchema("delete_file", "Permanently delete a file from Drive.", [
                ParamSpec("file_id", "string", required=True, description="Google Drive file ID."),
            ]),
            ActionSchema("share_file", "Share a file with a specific user.", [
                ParamSpec("file_id", "string", required=True,  description="Google Drive file ID."),
                ParamSpec("email",   "string", required=True,  description="Email address of the person to share with."),
                ParamSpec("role",    "string", required=False, description="Permission role.", default="reader",
                          choices=list(_ALLOWED_ROLES)),
                ParamSpec("notify",  "boolean", required=False, description="Send notification email.", default=True),
            ]),
            ActionSchema("get_file_metadata", "Get metadata for a specific file.", [
                ParamSpec("file_id", "string", required=True, description="Google Drive file ID."),
            ]),
            ActionSchema("move_file", "Move a file to a different folder.", [
                ParamSpec("file_id",          "string", required=True, description="Google Drive file ID to move."),
                ParamSpec("destination_folder_id", "string", required=True, description="Target folder ID."),
            ]),
        ]

    # ── Dispatch ──────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> PluginResult:
        actions = {
            "list_files":        self._list_files,
            "search_files":      self._search_files,
            "upload_file":       self._upload_file,
            "download_file":     self._download_file,
            "delete_file":       self._delete_file,
            "share_file":        self._share_file,
            "get_file_metadata": self._get_file_metadata,
            "move_file":         self._move_file,
        }
        if action not in actions:
            return self._unknown_action(action)
        return actions[action](params)

    # ── Actions ───────────────────────────────────────────────────────────

    @with_retry()
    def _list_files(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("list_files")
        page_size = min(int(params.get("page_size", 20)), 1000)
        q_parts = ["trashed = false"]
        if params.get("folder_id"):
            q_parts.append(f"'{params['folder_id']}' in parents")
        results = self.service.files().list(
            pageSize=page_size,
            q=" and ".join(q_parts),
            fields="files(id, name, mimeType, webViewLink, modifiedTime, size)",
        ).execute()
        files = results.get("files", [])
        return self._ok("list_files", f"Found {len(files)} files.", data=files)

    @with_retry()
    def _search_files(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("search_files")
        query = params.get("query", "").strip()
        if not query:
            return self._missing_param("search_files", "query")
        # Sanitize: escape single quotes to prevent Drive query injection
        safe_query = query.replace("\\", "\\\\").replace("'", "\\'")
        q_parts = [f"name contains '{safe_query}'", "trashed = false"]
        if params.get("mime_type"):
            mime = params["mime_type"].replace("'", "\\'")
            q_parts.append(f"mimeType = '{mime}'")
        if params.get("folder_id"):
            q_parts.append(f"'{params['folder_id']}' in parents")
        results = self.service.files().list(
            q=" and ".join(q_parts),
            fields="files(id, name, mimeType, webViewLink, modifiedTime, size)",
        ).execute()
        files = results.get("files", [])
        return self._ok("search_files", f"Found {len(files)} matching files.", data=files)

    @with_retry()
    def _upload_file(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("upload_file")
        name = params.get("name", "").strip()
        if not name:
            return self._missing_param("upload_file", "name")
        from googleapiclient.http import MediaInMemoryUpload
        data  = (params.get("content") or "").encode()
        media = MediaInMemoryUpload(data, mimetype=params.get("mimetype", "text/plain"))
        parents = [params["folder_id"]] if params.get("folder_id") else []
        file = self.service.files().create(
            body={"name": name, "parents": parents},
            media_body=media,
            fields="id,webViewLink,name,mimeType",
        ).execute()
        return self._ok("upload_file", f"Uploaded: {name}",
                        data={"file_id": file["id"], "name": file["name"]},
                        url=file.get("webViewLink"))

    @with_retry()
    def _download_file(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("download_file")
        file_id = params.get("file_id", "").strip()
        if not file_id:
            return self._missing_param("download_file", "file_id")
        content = self.service.files().get_media(fileId=file_id).execute()
        return self._ok("download_file", "File downloaded.",
                        data={"content": content.decode(errors="replace")})

    @with_retry()
    def _delete_file(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("delete_file")
        file_id = params.get("file_id", "").strip()
        if not file_id:
            return self._missing_param("delete_file", "file_id")
        self.service.files().delete(fileId=file_id).execute()
        return self._ok("delete_file", f"File {file_id} permanently deleted.")

    @with_retry()
    def _share_file(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("share_file")
        file_id = params.get("file_id", "").strip()
        email   = params.get("email", "").strip()
        role    = params.get("role", "reader")
        if not file_id:
            return self._missing_param("share_file", "file_id")
        if not email:
            return self._missing_param("share_file", "email")
        if not self._valid_email(email):
            return self._fail("share_file", f"Invalid email address: '{email}'",
                              error_code="INVALID_PARAMS")
        if role not in _ALLOWED_ROLES:
            return self._fail("share_file",
                              f"Invalid role '{role}'. Allowed: {_ALLOWED_ROLES}",
                              error_code="INVALID_PARAMS")
        self.service.permissions().create(
            fileId=file_id,
            body={"type": "user", "role": role, "emailAddress": email},
            sendNotificationEmail=params.get("notify", True),
        ).execute()
        return self._ok("share_file", f"File shared with {email} as '{role}'.")

    @with_retry()
    def _get_file_metadata(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("get_file_metadata")
        file_id = params.get("file_id", "").strip()
        if not file_id:
            return self._missing_param("get_file_metadata", "file_id")
        file = self.service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, webViewLink, modifiedTime, size, createdTime, owners",
        ).execute()
        return self._ok("get_file_metadata", f"Metadata for: {file.get('name')}",
                        data=file, url=file.get("webViewLink"))

    @with_retry()
    def _move_file(self, params: dict) -> PluginResult:
        if not self.service:
            return self._not_connected("move_file")
        file_id   = params.get("file_id", "").strip()
        dest_id   = params.get("destination_folder_id", "").strip()
        if not file_id:
            return self._missing_param("move_file", "file_id")
        if not dest_id:
            return self._missing_param("move_file", "destination_folder_id")
        # Retrieve current parents to remove them
        file = self.service.files().get(fileId=file_id, fields="parents").execute()
        prev_parents = ",".join(file.get("parents", []))
        updated = self.service.files().update(
            fileId=file_id,
            addParents=dest_id,
            removeParents=prev_parents,
            fields="id, parents, webViewLink",
        ).execute()
        return self._ok("move_file", f"File {file_id} moved to folder {dest_id}.",
                        url=updated.get("webViewLink"))
