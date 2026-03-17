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

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import uvicorn
import os
import httpx
import tempfile
import shutil
import pathlib

from main import EnterpriseAIAssistant
from security.rbac import Role
from security.clerk_auth import verify_clerk_token, ClerkTokenPayload
from security.nova_jwt  import create_employee_token, verify_employee_token
from utils.email_sender import send_invite_email

app       = FastAPI(title="Nova AI — Enterprise Assistant", version="2.0.0")
assistant = EnterpriseAIAssistant()

# ── Upload / Ingestion Limits & Validation ───────────────────────────────────
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))  # 20 MB default
MAX_DOCS_PER_TENANT = int(os.getenv("MAX_DOCS_PER_TENANT", "1000"))
ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".csv",
    ".txt",
    ".json",
    ".xml",
    ".md",
    ".jpg",
    ".jpeg",
}

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
    history:    Optional[list] = None   # [{role: 'user'|'assistant', content: str}]

class ChatResponse(BaseModel):
    response:   str
    session_id: Optional[str]
    tenant_id:  str
    role:       str
    sources:    list = []
    tools_used: list = []   # [{plugin, action, success, message}]

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
        history     = request.history or [],
    )

    # Pull sources from the last retrieval for the frontend to display
    sources: list = []
    try:
        ctx_sources = getattr(assistant, "_last_sources", [])
        sources = ctx_sources or []
    except Exception:
        pass

    return ChatResponse(
        response   = response,
        session_id = request.session_id,
        tenant_id  = token.tenant_id,
        role       = token.role,
        sources    = sources,
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
    if len(request.sender_password.replace(" ", "")) < 8:
        raise HTTPException(
            status_code=400,
            detail="Gmail App Password must be at least 8 characters. "
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


@app.post("/test-email")
async def test_email(
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """
    Admin-only: Send a test email to themselves to verify Gmail credentials work.
    """
    if token.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can send test emails.")

    email_cfg = assistant.tenant_manager.get_email_config(token.tenant_id)
    if not email_cfg:
        raise HTTPException(
            status_code=400,
            detail="No email config found. Please save your Gmail credentials first."
        )

    sent = send_invite_email(
        to_email        = token.email or token.user_id,
        company_name    = "Nova AI",
        join_code       = "TEST-EMAIL",
        role            = token.role,
        invited_by      = "Nova AI (test)",
        sender_email    = email_cfg.get("sender_email", ""),
        sender_password = email_cfg.get("sender_password", ""),
    )

    if sent:
        return {"status": "sent", "message": f"Test email sent to {token.email or token.user_id}."}
    else:
        raise HTTPException(
            status_code=502,
            detail="Failed to send test email. Check your Gmail address and App Password. "
                   "Make sure 2-Step Verification is enabled and you are using a Gmail App Password "
                   "(not your normal Gmail password)."
        )


@app.get("/metrics")
async def metrics(
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """LLMOps metrics — scoped to the authenticated tenant."""
    return assistant.get_metrics()


@app.post("/upload")
async def upload_document(
    file:     UploadFile = File(...),
    category: str        = Form("general"),
    db_type:  str        = Form("public"),
    token:    ClerkTokenPayload = Depends(get_current_user),
):
    """
    Admin-only: upload a file directly from the browser.
    Applies server-side validation for file type, size, and per-tenant limits,
    then saves to a temp file, runs the ingestion pipeline, and deletes the temp file.
    """
    if token.role != "admin":
        raise HTTPException(status_code=403,
                            detail="Only admins can upload documents.")
    if db_type not in ("public", "private"):
        raise HTTPException(status_code=400,
                            detail="db_type must be 'public' or 'private'.")

    # ── Validate file extension ──────────────────────────────────────────────
    filename = file.filename or "upload"
    suffix   = pathlib.Path(filename).suffix.lower() or ".bin"
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_UPLOAD_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed types: {allowed}",
        )

    # ── Validate file size ───────────────────────────────────────────────────
    try:
        file.file.seek(0, os.SEEK_END)
        size_bytes = file.file.tell()
        file.file.seek(0)
    except Exception:
        size_bytes = 0

    if size_bytes and size_bytes > MAX_UPLOAD_BYTES:
        max_mb = round(MAX_UPLOAD_BYTES / (1024 * 1024))
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {max_mb} MB.",
        )

    # ── Per-tenant document count limit ──────────────────────────────────────
    existing_docs = assistant.list_documents(token.tenant_id)
    if len(existing_docs) >= MAX_DOCS_PER_TENANT:
        raise HTTPException(
            status_code=400,
            detail=(
                "Document limit reached for this workspace. "
                "Please archive or delete older documents before uploading more."
            ),
        )

    # Use validated suffix (falls back to .bin only if none)
    suffix   = suffix or ".bin"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        result = assistant.ingest_document(
            file_path         = tmp_path,
            tenant_id         = token.tenant_id,
            category          = category,
            uploaded_by       = token.user_id,
            db_type           = db_type,
            original_filename = file.filename or "",
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if result.get("status") == "failed":
        raise HTTPException(status_code=400, detail=result.get("reason"))
    if result.get("status") == "blocked":
        raise HTTPException(status_code=422, detail=result.get("reason"))

    return result


@app.get("/documents")
async def list_documents(
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """List all ingested source files for this tenant (both DBs)."""
    docs = assistant.list_documents(token.tenant_id)
    return {"documents": docs}



# ── Tools / Plugins API ───────────────────────────────────────────────────

@app.get("/tools")
async def list_tools(
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """List all available tools (plugins) and their actions."""
    plugins = assistant.plugins.describe_all()
    return {"tools": plugins}


@app.get("/tools/health")
async def tools_health(
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """Check connectivity / health status of all tools."""
    if token.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Managers and admins only.")
    report = assistant.plugins.health_report()
    return {"health": report}


@app.get("/tools/connection-status")
async def tools_connection_status(
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """Check if Google Workspace is connected (token file exists and is valid)."""
    import os
    token_file = os.getenv("GOOGLE_TOKEN_FILE", "./credentials/google_token.json")
    connected  = os.path.exists(token_file)
    detail     = "Connected" if connected else "Not connected"
    return {"connected": connected, "detail": detail, "token_file": token_file}


@app.get("/tools/connect/google")
async def connect_google(
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """
    Generate a Google OAuth authorisation URL.
    Works with both 'installed' (desktop) and 'web' OAuth client types.
    """
    if token.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can connect Google Workspace.")

    import os
    import json
    from google_auth_oauthlib.flow import Flow

    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "./Backend/credentials/google_credentials.json")
    if not os.path.exists(creds_file):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Google credentials file not found at: {creds_file}. "
                "Download from Google Cloud Console → APIs & Services → Credentials "
                "→ OAuth 2.0 Client IDs → Download JSON → save as Backend/credentials/google_credentials.json"
            ),
        )

    # Detect credential type (installed vs web)
    with open(creds_file) as f:
        cred_data = json.load(f)
    cred_type = "installed" if "installed" in cred_data else "web"

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://mail.google.com/",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/meetings.space.created",
    ]

    # For installed apps, we use the loopback redirect
    REDIRECT_URI = (
        "http://localhost:8000/tools/callback/google"
        if cred_type == "web"
        else os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/tools/callback/google")
    )

    try:
        flow = Flow.from_client_secrets_file(creds_file, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        auth_url, _ = flow.authorization_url(
            prompt="consent",
            access_type="offline",
            include_granted_scopes="true",
        )
        return {"auth_url": auth_url, "cred_type": cred_type}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate auth URL: {e}")


@app.get("/tools/callback/google")
async def google_oauth_callback(
    code: str,
    state: Optional[str] = None,
):
    """
    OAuth callback — exchanges the code for tokens and saves them.
    Accessible without auth since Google redirects here directly.
    """
    import os, json
    from google_auth_oauthlib.flow import Flow

    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "./credentials/google_credentials.json")
    token_file = os.getenv("GOOGLE_TOKEN_FILE", "./credentials/google_token.json")
    REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/tools/callback/google")

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/calendar",
    ]

    if not os.path.exists(creds_file):
        raise HTTPException(status_code=400, detail="credentials/google_credentials.json not found.")

    try:
        flow = Flow.from_client_secrets_file(creds_file, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Ensure credentials directory exists
        os.makedirs(os.path.dirname(token_file) if os.path.dirname(token_file) else ".", exist_ok=True)

        # Save token JSON
        token_data = {
            "token":         creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri":     creds.token_uri,
            "client_id":     creds.client_id,
            "client_secret": creds.client_secret,
            "scopes":        list(creds.scopes) if creds.scopes else [],
        }
        with open(token_file, "w") as f:
            json.dump(token_data, f, indent=2)

        logger.info(f"[GoogleOAuth] Token saved to {token_file}")

        # Re-initialise all plugins so they pick up the new token
        assistant.plugins._register_all()

        # Redirect to dashboard tools page
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="http://localhost:5173/dashboard/tools?connected=1")

    except Exception as e:
        logger.error(f"[GoogleOAuth] Callback error: {e}")
        raise HTTPException(status_code=400, detail=f"OAuth failed: {e}")


class ToolExecuteRequest(BaseModel):
    plugin: str
    action: str
    params: dict = {}

@app.post("/tools/execute")
async def execute_tool(
    request: ToolExecuteRequest,
    token: ClerkTokenPayload = Depends(get_current_user),
):
    """Execute a specific plugin action."""
    if token.role not in ("admin", "manager", "team_lead"):
        raise HTTPException(status_code=403,
                            detail="You don't have permission to execute tools.")
    result = assistant.plugins.execute(request.plugin, request.action, request.params)
    return {
        "plugin":  result.plugin,
        "action":  result.action,
        "success": result.success,
        "message": result.message,
        "data":    result.data,
    }


# ── Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
