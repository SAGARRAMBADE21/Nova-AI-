"""
api/server.py
FastAPI REST Server — Multi-Tenant, Clerk JWT auth
Endpoints:
  POST /onboard       — create company workspace (public)
  POST /invite-user   — admin: add user with role
  GET  /users         — admin: list all users in workspace
  POST /chat          — all roles: query the AI assistant
  POST /ingest        — admin: upload document to public or private DB
  GET  /metrics       — all roles: LLMOps metrics (tenant-scoped)
  GET  /health        — public: health check
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
import uvicorn
import os
import httpx

from main import EnterpriseAIAssistant
from security.rbac import Role
from security.clerk_auth import verify_clerk_token, ClerkTokenPayload
from security.nova_jwt  import create_employee_token, verify_employee_token

app       = FastAPI(title="Nova AI — Enterprise Assistant", version="2.0.0")
assistant = EnterpriseAIAssistant()

# ── Unified auth dependency ───────────────────────────────────────────────
# Accepts EITHER:
#   - Clerk JWT   (admin / manager / team_lead — signed by Clerk RS256)
#   - Nova JWT    (employee — signed by NOVA_JWT_SECRET HS256 via /join)

from fastapi import Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

_bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> ClerkTokenPayload:
    """
    Try Nova JWT first (employee path), then Clerk JWT (admin path).
    Returns a ClerkTokenPayload for both — same interface throughout.
    """
    if credentials and credentials.credentials:
        raw_token = credentials.credentials

        # 1. Try Nova employee JWT (join code + email flow)
        nova_payload = verify_employee_token(raw_token)
        if nova_payload:
            return ClerkTokenPayload(
                user_id   = nova_payload["email"],
                org_id    = nova_payload["tenant_id"],
                org_role  = f"org:{nova_payload['role']}",
                email     = nova_payload["email"],
                tenant_id = nova_payload["tenant_id"],
                role      = nova_payload["role"],
            )

    # 2. Fall back to Clerk JWT (admin / manager path)
    return verify_clerk_token(credentials)


# ── Request / Response Models ─────────────────────────────────────────────

class OnboardRequest(BaseModel):
    company_name: str
    admin_email:  str
    tenant_id:    str          # Clerk Organization ID (org_id)

class InviteUserRequest(BaseModel):
    email: str
    role:  str = "employee"    # employee | manager | team_lead | admin

class ChatRequest(BaseModel):
    prompt:     str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response:   str
    session_id: Optional[str]
    tenant_id:  str
    role:       str

class IngestRequest(BaseModel):
    file_path: str
    category:  str = "general"
    db_type:   str = "public"  # 'public' or 'private'

class JoinRequest(BaseModel):
    join_code: str      # unique company code (e.g. 'ACMEXK7P12')
    email:     str      # work email
    password:  str      # user's password

class RegisterRequest(BaseModel):
    join_code: str      # company join code
    email:     str      # work email
    password:  str      # choose a password (first time setup)


# ── Public Endpoints ──────────────────────────────────────────────────────

@app.post("/onboard")
async def onboard(request: OnboardRequest):
    """
    Create a new company workspace.
    Called once by the company owner when they first sign up.
    """
    result = assistant.onboard_company(
        company_name = request.company_name,
        admin_email  = request.admin_email,
        tenant_id    = request.tenant_id,
    )
    return result


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0"}


@app.post("/register")
async def register(request: RegisterRequest):
    """
    First-time account setup for non-admin users (employee / manager / team_lead).
    Admin must have already added the email via /invite-user.

    Flow:
      1. Admin invites: POST /invite-user  { email, role }  → status='invited'
      2. Employee registers: POST /register { join_code, email, password }
         → sets password, status becomes 'active'
      3. Employee logs in: POST /join { join_code, email, password } → Nova JWT
    """
    email = request.email.lower().strip()

    # 1. Verify join code
    company = assistant.tenant_manager.get_company_by_code(request.join_code)
    if not company:
        raise HTTPException(status_code=404,
                            detail="Invalid join code.")

    # 2. Check the email was invited
    user = assistant.tenant_manager.get_user(company["tenant_id"], email)
    if not user:
        raise HTTPException(status_code=403,
                            detail="This email has not been invited. Contact your admin.")

    # 3. Block if already registered
    if user.get("status") == "active" and user.get("password_hash"):
        raise HTTPException(status_code=409,
                            detail="Account already registered. Please use /join to login.")

    # 4. Set password
    if len(request.password) < 8:
        raise HTTPException(status_code=400,
                            detail="Password must be at least 8 characters.")

    assistant.tenant_manager.set_password(company["tenant_id"], email, request.password)

    return {
        "message": f"Account created for {email} in {company['company_name']}. "
                   f"You can now login via /join.",
        "role":    user["role"],
    }


@app.post("/join")
async def join_workspace(request: JoinRequest):
    """
    Login for non-admin users (employee / manager / team_lead).
    NO Clerk required — uses company join code + email + password.
    Returns a Nova-signed JWT valid for 12 hours.
    """
    email = request.email.lower().strip()

    # 1. Find company by join code
    company = assistant.tenant_manager.get_company_by_code(request.join_code)
    if not company:
        raise HTTPException(status_code=404,
                            detail="Invalid join code. Check with your admin.")

    # 2. Check user is invited / registered
    user = assistant.tenant_manager.get_user(company["tenant_id"], email)
    if not user:
        raise HTTPException(status_code=403,
                            detail="Email not found in this workspace. Contact your admin.")

    # 3. If not yet registered, prompt to register first
    if user.get("status") == "invited" or not user.get("password_hash"):
        raise HTTPException(status_code=403,
                            detail="Account not set up yet. Please register first at /register.")

    # 4. Verify password
    if not assistant.tenant_manager.verify_user_password(
        company["tenant_id"], email, request.password
    ):
        raise HTTPException(status_code=401,
                            detail="Incorrect password.")

    # 5. Issue Nova JWT (12h)
    token = create_employee_token(
        email     = email,
        tenant_id = company["tenant_id"],
        role      = user["role"],
    )

    return {
        "token":        token,
        "company_name": company["company_name"],
        "role":         user["role"],
        "message":      f"Welcome back to {company['company_name']}!",
    }


# ── Authenticated Endpoints ───────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """
    Send a query to ARIA.
    Role and tenant_id are extracted automatically from the Clerk JWT.
    """
    try:
        role = Role(token.role)
    except ValueError:
        role = Role.EMPLOYEE

    response = assistant.chat(
        user_prompt = request.prompt,
        user_id     = token.user_id,
        user_role   = role,
        tenant_id   = token.tenant_id,
        session_id  = request.session_id,
    )

    return ChatResponse(
        response   = response,
        session_id = request.session_id,
        tenant_id  = token.tenant_id,
        role       = token.role,
    )


@app.post("/ingest")
async def ingest(
    request: IngestRequest,
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """
    Admin-only: ingest a document into the tenant's knowledge base.
    db_type='public'  → all employees can read
    db_type='private' → managers, team leads, admins only
    """
    if token.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can ingest documents.",
        )

    if request.db_type not in ("public", "private"):
        raise HTTPException(
            status_code=400,
            detail="db_type must be 'public' or 'private'.",
        )

    result = assistant.ingest_document(
        file_path   = request.file_path,
        tenant_id   = token.tenant_id,
        category    = request.category,
        uploaded_by = token.user_id,
        db_type     = request.db_type,
    )

    if result.get("status") == "failed":
        raise HTTPException(status_code=400, detail=result.get("reason"))
    if result.get("status") == "blocked":
        raise HTTPException(status_code=422, detail=result.get("reason"))

    return result


@app.post("/invite-user")
async def invite_user(
    request: InviteUserRequest,
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """
    Admin-only: add a user to the company workspace with a role.
    In production: also call Clerk API to send an email invite.
    """
    if token.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can invite users.",
        )

    valid_roles = {"employee", "manager", "team_lead", "admin"}
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {valid_roles}",
        )

    result = assistant.invite_user(
        tenant_id  = token.tenant_id,
        email      = request.email,
        role       = request.role,
        invited_by = token.user_id,
    )

    # Also send Clerk organization invitation (real email)
    clerk_secret = os.getenv("CLERK_SECRET_KEY", "")
    if clerk_secret and token.tenant_id.startswith("org_"):
        try:
            async with httpx.AsyncClient() as http:
                resp = await http.post(
                    f"https://api.clerk.com/v1/organizations/{token.tenant_id}/invitations",
                    headers={
                        "Authorization": f"Bearer {clerk_secret}",
                        "Content-Type":  "application/json",
                    },
                    json={
                        "email_address": request.email,
                        "role":          f"org:{request.role}",
                    },
                    timeout=10,
                )
            if resp.status_code in (200, 201):
                result["clerk_invite"] = "sent"
            else:
                result["clerk_invite"] = f"skipped ({resp.status_code})"
        except Exception as e:
            result["clerk_invite"] = f"error: {e}"
    else:
        result["clerk_invite"] = "skipped (dev mode)"

    return result


@app.get("/users")
async def list_users(
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """Admin-only: list all users in this company workspace."""
    if token.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can view user lists.",
        )

    users = assistant.list_users(token.tenant_id)
    return {"tenant_id": token.tenant_id, "users": users}


@app.get("/metrics")
async def metrics(
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """LLMOps metrics — scoped to the authenticated tenant."""
    return assistant.get_metrics()


# ── Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
