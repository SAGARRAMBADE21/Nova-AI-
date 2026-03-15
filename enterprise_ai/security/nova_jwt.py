"""
security/nova_jwt.py
Nova AI — Custom JWT for ALL company users (no Clerk required).

Flow:
  1. User enters join_code + email + password  →  POST /join
  2. Backend verifies credentials against MongoDB
  3. Backend issues a Nova-signed JWT (HS256, NOVA_JWT_SECRET)
  4. User uses this token as Bearer on all protected endpoints

All roles (employee, team_lead, manager, admin) use Nova JWT.
Clerk JWT is used only by developers for internal tooling.
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

def create_employee_token(email:        str,
                          tenant_id:    str,
                          role:         str,
                          company_name: str = "") -> str:
    """
    Issue a signed JWT for a user who logged in via join code + email + password.
    Token is signed with NOVA_JWT_SECRET (HS256).
    All company roles use this token: employee, team_lead, manager, admin.
    """
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_H)
    payload = {
        "sub":          email,
        "email":        email,
        "tenant_id":    tenant_id,
        "role":         role,
        "company_name": company_name,   # included for context-aware responses
        "iss":          "nova-ai",       # issuer flag — identifies as a Nova token
        "exp":          expire,
    }
    token = jwt.encode(payload, _secret(), algorithm=ALGORITHM)
    logger.info(
        f"[NovaJWT] Token issued | email={email} | "
        f"tenant={tenant_id} | role={role} | company={company_name} "
        f"| expires={expire.isoformat()}"
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
