"""
security/clerk_auth.py
Clerk JWT verification — FastAPI dependency.

Extracts tenant_id (org_id) and role (org_role) from Clerk-issued JWTs.

Dev mode:
    If CLERK_JWKS_URL is not set, returns a mock admin payload using
    DEV_TENANT_ID env var — safe for local development.

Production:
    Set CLERK_JWKS_URL to your Clerk instance JWKS endpoint, e.g.:
    https://<your-domain>.clerk.accounts.dev/.well-known/jwks.json
"""

import os
import logging
from functools import lru_cache
from typing import Optional

import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)

# Clerk org role → internal role name mapping
CLERK_ROLE_MAP: dict[str, str] = {
    "org:admin":     "admin",
    "org:manager":   "manager",
    "org:team_lead": "team_lead",
    "org:member":    "employee",
}


# ── Token payload ─────────────────────────────────────────────────────────

class ClerkTokenPayload:
    """Parsed Clerk JWT — available via Depends(verify_clerk_token)."""

    def __init__(self, user_id: str, org_id: str, org_role: str,
                 email: str, tenant_id: str, role: str):
        self.user_id   = user_id
        self.org_id    = org_id
        self.org_role  = org_role
        self.email     = email
        self.tenant_id = tenant_id   # == org_id (Clerk Organization ID)
        self.role      = role        # mapped internal role

    def __repr__(self):
        return (
            f"ClerkTokenPayload(user={self.user_id}, "
            f"tenant={self.tenant_id}, role={self.role})"
        )


# ── JWKS (cached) ─────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    """Fetch Clerk JWKS once and cache for process lifetime."""
    jwks_url = os.getenv("CLERK_JWKS_URL", "")
    if not jwks_url:
        return {}
    resp = httpx.get(jwks_url, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ── FastAPI dependency ────────────────────────────────────────────────────

def verify_clerk_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(
        security_scheme
    ),
) -> ClerkTokenPayload:
    """
    FastAPI dependency — verifies a Clerk-issued JWT.

    Usage:
        @app.post("/chat")
        async def chat(token: ClerkTokenPayload = Depends(verify_clerk_token)):
            tenant_id = token.tenant_id
            role      = token.role
    """
    jwks_url = os.getenv("CLERK_JWKS_URL", "")

    # ── Dev / local mode (no Clerk configured) ────────────────────────────
    if not jwks_url:
        logger.warning(
            "[ClerkAuth] CLERK_JWKS_URL not set — running in dev mode."
        )
        return ClerkTokenPayload(
            user_id   = "dev_user_001",
            org_id    = os.getenv("DEV_TENANT_ID", "dev_tenant"),
            org_role  = "org:admin",
            email     = "dev@example.com",
            tenant_id = os.getenv("DEV_TENANT_ID", "dev_tenant"),
            role      = "admin",
        )

    # ── Production: verify JWT ────────────────────────────────────────────
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required.",
        )

    token = credentials.credentials

    try:
        jwks   = _get_jwks()
        header = jwt.get_unverified_header(token)

        # Match key by kid
        key = next(
            (k for k in jwks.get("keys", [])
             if k.get("kid") == header.get("kid")),
            None,
        )
        if not key:
            raise HTTPException(
                status_code=401,
                detail="JWT signing key not found in JWKS.",
            )

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )

        org_id   = payload.get("org_id", "")
        org_role = payload.get("org_role", "")
        email    = payload.get("email", "")
        sub      = payload.get("sub", "")

        if not org_id:
            raise HTTPException(
                status_code=403,
                detail=(
                    "No organization found in token. "
                    "Please join a company workspace first."
                ),
            )

        role = CLERK_ROLE_MAP.get(org_role, "employee")

        logger.info(
            f"[ClerkAuth] Token verified | user={sub} "
            f"| tenant={org_id} | role={role}"
        )
        return ClerkTokenPayload(
            user_id=sub, org_id=org_id, org_role=org_role,
            email=email, tenant_id=org_id, role=role,
        )

    except JWTError as e:
        logger.error(f"[ClerkAuth] JWT error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
