"""
security/nova_jwt.py
Nova AI — Custom JWT for employee login (no Clerk required).

Flow:
  1. Employee enters join_code + email  →  POST /join
  2. Backend verifies against MongoDB users collection
  3. Backend issues a Nova-signed JWT (HS256, NOVA_JWT_SECRET)
  4. Employee uses this token as Bearer on POST /chat

Admin/Manager/TeamLead still use Clerk JWT (RS256).
The unified `get_current_user` dependency in server.py
tries Clerk JWT first, falls back to Nova JWT.
"""

import os
import logging
from datetime import datetime, timedelta

from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

ALGORITHM       = "HS256"
TOKEN_EXPIRE_H  = 12   # hours


def _secret() -> str:
    secret = os.getenv("NOVA_JWT_SECRET", "")
    if not secret:
        raise RuntimeError(
            "NOVA_JWT_SECRET is not set in .env. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return secret


# ── Issue token ───────────────────────────────────────────────────────────

def create_employee_token(email: str, tenant_id: str, role: str) -> str:
    """
    Issue a signed JWT for an employee who logged in via join code + email.
    Token is signed with NOVA_JWT_SECRET (HS256) — not Clerk.
    """
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_H)
    payload = {
        "sub":       email,
        "email":     email,
        "tenant_id": tenant_id,
        "role":      role,
        "iss":       "nova-ai",          # issuer flag — tells auth layer it's a Nova token
        "exp":       expire,
    }
    token = jwt.encode(payload, _secret(), algorithm=ALGORITHM)
    logger.info(
        f"[NovaJWT] Token issued | email={email} | "
        f"tenant={tenant_id} | role={role} | expires={expire.isoformat()}"
    )
    return token


# ── Verify token ──────────────────────────────────────────────────────────

def verify_employee_token(token: str) -> dict | None:
    """
    Verify a Nova-issued employee JWT.
    Returns the decoded payload dict, or None if invalid.
    """
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
        if payload.get("iss") != "nova-ai":
            return None    # not a Nova token — skip
        return payload
    except JWTError as e:
        logger.debug(f"[NovaJWT] Not a valid Nova token: {e}")
        return None
