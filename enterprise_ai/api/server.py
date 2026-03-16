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
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import uvicorn
import os
import httpx

from main import EnterpriseAIAssistant
from security.rbac import Role
from security.clerk_auth import verify_clerk_token, ClerkTokenPayload
from security.nova_jwt  import create_employee_token, verify_employee_token
from utils.email_sender import send_invite_email

app       = FastAPI(title="Nova AI — Enterprise Assistant", version="2.0.0")
assistant = EnterpriseAIAssistant()

# ── CORS — allow Vite dev server ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ── Auth note ────────────────────────────────────────────────────────────
# Clerk is used ONLY by developers for internal platform management.
# ALL company users (admin, manager, team_lead, employee) authenticate via:
#   POST /join  { join_code, email, password }  →  Nova JWT
# ───────────────────────────────────────────────────────────────────────

# ── Request / Response Models ─────────────────────────────────────────────

class OnboardRequest(BaseModel):
    company_name:   str
    admin_email:    str
    admin_password: str     # admin sets their password at registration time
    # tenant_id is auto-generated — no Clerk required

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
    Company owner creates their workspace on Nova AI.
    No Clerk required — generates tenant_id automatically.

    Returns join_code — share this code with your team.
    Admin can immediately login via POST /join with their email + password.
    """
    import uuid

    if len(request.admin_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Admin password must be at least 8 characters."
        )

    # Auto-generate a unique tenant ID (no Clerk needed)
    tenant_id = f"tenant_{uuid.uuid4().hex[:16]}"

    # Create company workspace
    result = assistant.onboard_company(
        company_name   = request.company_name,
        admin_email    = request.admin_email,
        tenant_id      = tenant_id,
    )

    # Create admin user with hashed password in MongoDB
    assistant.tenant_manager.add_user(
        tenant_id = tenant_id,
        email     = request.admin_email.lower().strip(),
        role      = "admin",
    )
    assistant.tenant_manager.set_password(
        tenant_id = tenant_id,
        email     = request.admin_email.lower().strip(),
        password  = request.admin_password,
    )

    return {
        "company_name": result["company_name"],
        "tenant_id":    tenant_id,
        "join_code":    result["join_code"],
        "message":      f"Workspace created! Share join code '"
                        f"{result['join_code']}' with your team. "
                        f"Login via POST /join with your email and password.",
    }


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

    # Send invite email FROM admin's own Gmail (fetched from MongoDB)
    company    = assistant.tenant_manager.get_company_by_tenant_id(token.tenant_id)
    email_cfg  = assistant.tenant_manager.get_email_config(token.tenant_id)
    if company:
        email_sent = send_invite_email(
            to_email        = request.email,
            company_name    = company["company_name"],
            join_code       = company["join_code"],
            role            = request.role,
            invited_by      = token.user_id,
            sender_email    = (email_cfg or {}).get("sender_email",    ""),
            sender_password = (email_cfg or {}).get("sender_password", ""),
        )
        result["invite_email"] = (
            "sent" if email_sent
            else "skipped — configure Gmail via POST /email-config"
        )
    else:
        result["invite_email"] = "skipped (company not found)"

    return result


@app.get("/users")
async def list_users(
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """Admin-only: list all users in this company workspace."""
    if token.role != "admin":
        raise HTTPException(status_code=403,
                            detail="Only admins can view user lists.")
    users = assistant.list_users(token.tenant_id)
    return {"tenant_id": token.tenant_id, "users": users}


class EmailConfigRequest(BaseModel):
    sender_email:    str   # admin's Gmail address
    sender_password: str   # Gmail App Password (16 chars, NOT normal password)

@app.post("/email-config")
async def set_email_config(
    request: EmailConfigRequest,
    token:   ClerkTokenPayload = Depends(get_current_user),
):
    """
    Admin sets their own Gmail for sending invite emails.
    Invite emails will come FROM this Gmail address.

    Gmail App Password setup:
      1. myaccount.google.com → Security → 2-Step Verification (enable)
      2. App Passwords → create one for 'Nova AI'
      3. Paste the 16-char code here as sender_password
    """
    if token.role != "admin":
        raise HTTPException(status_code=403,
                            detail="Only admins can configure email settings.")

    if "@" not in request.sender_email:
        raise HTTPException(status_code=400, detail="Invalid email address.")
    if len(request.sender_password.replace(" ", "")) < 16:
        raise HTTPException(
            status_code=400,
            detail="Gmail App Password must be 16 characters. "
                   "Get it at myaccount.google.com → Security → App Passwords."
        )

    assistant.tenant_manager.set_email_config(
        tenant_id    = token.tenant_id,
        sender_email = request.sender_email,
        app_password = request.sender_password.replace(" ", ""),  # strip spaces
    )
    return {
        "message": f"Email configured. Invites will now be sent from {request.sender_email}.",
        "sender":  request.sender_email,
    }


@app.get("/metrics")
async def metrics(
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """LLMOps metrics — scoped to the authenticated tenant."""
    return assistant.get_metrics()


# ── Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
