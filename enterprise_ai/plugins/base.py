"""
plugins/base.py
Shared base classes, result types, retry decorator, and schema definitions for all plugins.
"""

import re
import time
import logging
import functools
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict

logger = logging.getLogger(__name__)


# ── Retry decorator ───────────────────────────────────────────────────────

def with_retry(max_attempts: int = 3, backoff: float = 1.0):
    """Exponential backoff retry for transient API errors (skips client/param errors)."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    # Don't retry on known non-transient errors
                    err_str = str(e).lower()
                    if any(kw in err_str for kw in ("invalid_params", "not_connected",
                                                    "400", "401", "403", "404")):
                        raise
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
    error_code: Optional[str] = None   # NOT_CONNECTED | INVALID_PARAMS | UNKNOWN_ACTION | INTERNAL_ERROR

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON-safe responses."""
        return {
            "plugin":     self.plugin,
            "action":     self.action,
            "success":    self.success,
            "message":    self.message,
            "data":       self.data,
            "url":        self.url,
            "error_code": self.error_code,
        }


# ── Parameter schema ──────────────────────────────────────────────────────

@dataclass
class ParamSpec:
    """Describes a single parameter accepted by a plugin action."""
    name:        str
    type:        str                    # "string" | "integer" | "boolean" | "list" | "dict"
    required:    bool = False
    description: str = ""
    default:     Any = None
    choices:     Optional[List[Any]] = None


@dataclass
class ActionSchema:
    """Schema for a single plugin action."""
    action:      str
    description: str
    params:      List[ParamSpec] = field(default_factory=list)

    def required_params(self) -> List[str]:
        return [p.name for p in self.params if p.required]

    def to_dict(self) -> dict:
        return {
            "action":      self.action,
            "description": self.description,
            "params": [
                {
                    "name":        p.name,
                    "type":        p.type,
                    "required":    p.required,
                    "description": p.description,
                    "default":     p.default,
                    "choices":     p.choices,
                }
                for p in self.params
            ],
        }


# ── Base plugin ───────────────────────────────────────────────────────────

class BasePlugin(ABC):
    name: str
    ACTIONS: List[str] = []

    @abstractmethod
    def execute(self, action: str, params: dict) -> PluginResult:
        pass

    def get_schema(self) -> List[ActionSchema]:
        """Return a list of ActionSchema objects describing every supported action.
        Subclasses should override this to provide rich schema information."""
        return []

    def describe(self) -> dict:
        """Return a JSON-serialisable description of the plugin."""
        return {
            "plugin":  self.name,
            "actions": [s.to_dict() for s in self.get_schema()],
        }

    def health_check(self) -> bool:
        return True

    def list_actions(self) -> List[str]:
        return self.ACTIONS

    # ── Validation helpers ────────────────────────────────────────────────

    def _validate(self, action: str, params: dict,
                  schema: ActionSchema) -> Optional["PluginResult"]:
        """Validate params against an ActionSchema.  Returns a failure PluginResult
        on the first violation, or None if all checks pass."""
        # Required fields
        for name in schema.required_params():
            if not params.get(name):
                return self._missing_param(action, name)
        # Type coercion / choice validation
        for spec in schema.params:
            val = params.get(spec.name)
            if val is None:
                continue
            if spec.choices and val not in spec.choices:
                return self._fail(
                    action,
                    f"'{spec.name}' must be one of: {spec.choices}. Got: '{val}'",
                    error_code="INVALID_PARAMS",
                )
        return None

    @staticmethod
    def _valid_email(email: str) -> bool:
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

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
