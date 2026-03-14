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

app       = FastAPI(title="Nova AI — Enterprise Assistant", version="2.0.0")
assistant = EnterpriseAIAssistant()


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
    join_code: str      # unique company code (e.g. 'ACME-XK7P')
    email:     str      # user's email address


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


@app.post("/join")
async def join_workspace(request: JoinRequest):
    """
    Verify a company join code + email and return workspace info.

    Flow:
      1. User enters join code + their email on the login page
      2. This endpoint looks up the company by join code
      3. Checks if this email has been invited to that workspace
      4. Returns tenant_id + role so the frontend can route the user
      After this, the user authenticates via Clerk (SSO) to get a JWT.
    """
    # 1. Find company by join code
    company = assistant.tenant_manager.get_company_by_code(request.join_code)
    if not company:
        raise HTTPException(
            status_code=404,
            detail="Invalid join code. Please check with your company admin.",
        )

    # 2. Check if this email was invited to this workspace
    user = assistant.tenant_manager.get_user(
        tenant_id = company["tenant_id"],
        email     = request.email.lower().strip(),
    )
    if not user:
        raise HTTPException(
            status_code=403,
            detail="This email has not been invited to this workspace. "
                   "Contact your admin.",
        )

    return {
        "company_name": company["company_name"],
        "tenant_id":    company["tenant_id"],
        "role":         user["role"],
        "status":       user["status"],
        "message":      f"Welcome to {company['company_name']}! "
                        f"Please sign in with Clerk to continue.",
    }


# ── Authenticated Endpoints ───────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    token: ClerkTokenPayload = Depends(verify_clerk_token),
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
    token: ClerkTokenPayload = Depends(verify_clerk_token),
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
    token: ClerkTokenPayload = Depends(verify_clerk_token),
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
    token: ClerkTokenPayload = Depends(verify_clerk_token),
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
    token: ClerkTokenPayload = Depends(verify_clerk_token),
):
    """LLMOps metrics — scoped to the authenticated tenant."""
    return assistant.get_metrics()


# ── Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
