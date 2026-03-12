"""
plugins/base.py
Shared base classes, result types, and retry decorator for all plugins.
"""

import time
import logging
import functools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, List

logger = logging.getLogger(__name__)


# ── Retry decorator ───────────────────────────────────────────────────────

def with_retry(max_attempts: int = 3, backoff: float = 1.0):
    """Exponential backoff retry for transient API errors."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_attempts:
                        wait = backoff * (2 ** (attempt - 1))
                        logger.warning(
                            f"[Retry] {fn.__qualname__} attempt {attempt}/{max_attempts} "
                            f"failed: {e}. Retrying in {wait}s..."
                        )
                        time.sleep(wait)
            raise last_exc
        return wrapper
    return decorator


# ── Plugin result ─────────────────────────────────────────────────────────

@dataclass
class PluginResult:
    plugin:     str
    action:     str
    success:    bool
    message:    str
    data:       Optional[Any] = None
    url:        Optional[str] = None
    error_code: Optional[str] = None   # NOT_CONNECTED | INVALID_PARAMS | UNKNOWN_ACTION


# ── Base plugin ───────────────────────────────────────────────────────────

class BasePlugin(ABC):
    name: str
    ACTIONS: List[str] = []

    @abstractmethod
    def execute(self, action: str, params: dict) -> PluginResult:
        pass

    def health_check(self) -> bool:
        return True

    def list_actions(self) -> List[str]:
        return self.ACTIONS

    # ── Result helpers ────────────────────────────────────────────────────

    def _ok(self, action: str, message: str,
            data=None, url: str = None) -> PluginResult:
        logger.info(f"[{self.name}] ✓ {action}: {message}")
        return PluginResult(self.name, action, True, message, data, url)

    def _fail(self, action: str, message: str,
              error_code: str = "ERROR") -> PluginResult:
        logger.error(f"[{self.name}] ✗ {action}: {message}")
        return PluginResult(self.name, action, False, message,
                            error_code=error_code)

    def _not_connected(self, action: str) -> PluginResult:
        return self._fail(action,
                          f"{self.name} is not connected. Check credentials in .env.",
                          error_code="NOT_CONNECTED")

    def _unknown_action(self, action: str) -> PluginResult:
        supported = ", ".join(self.ACTIONS) or "none"
        return self._fail(action,
                          f"Unknown action '{action}'. Supported: {supported}",
                          error_code="UNKNOWN_ACTION")

    def _missing_param(self, action: str, param: str) -> PluginResult:
        return self._fail(action,
                          f"Missing required parameter: '{param}'",
                          error_code="INVALID_PARAMS")

    # ── Shared Google auth ────────────────────────────────────────────────

    @staticmethod
    def _google_creds():
        """Load and auto-refresh Google OAuth credentials."""
        import os
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        token_file = os.getenv("GOOGLE_TOKEN_FILE", "")
        if not token_file or not __import__('os').path.exists(token_file):
            return None
        creds = Credentials.from_authorized_user_file(token_file)
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"[GoogleAuth] Token refresh failed: {e}")
        return creds if creds and creds.valid else None
