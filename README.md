<div align="center">

<br />

# ✦ Nova AI

### Enterprise AI Assistant — Secure · Multi-Tenant · RAG-Powered

<br />

[![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB_Atlas-47A248?style=flat-square&logo=mongodb&logoColor=white)](https://cloud.mongodb.com)
[![OpenAI](https://img.shields.io/badge/GPT--4-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

<br />

> Give every company their own private AI assistant — scoped to their documents,
> isolated from others, with role-based access so sensitive data stays protected.

<br />

</div>

---

## What is Nova AI?

Nova AI is a **production-ready, multi-tenant AI assistant** built for enterprises. Each company gets a completely isolated workspace. Employees can ask questions and get answers drawn exclusively from their own company's uploaded documents.

Unlike generic AI tools, Nova AI **never mixes data between companies** and **physically separates confidential documents** from regular ones — employees can't access them even if they try.

---

## How It Works

```
 Company Owner
      │
      │  POST /onboard  →  workspace created, join code issued
      │
      ▼
 ┌──────────────────────────────────────────────────────────────┐
 │                     Nova AI Platform                         │
 │                                                              │
 │  Admin Dashboard                                             │
 │  ├── Upload documents  →  public or confidential DB          │
 │  ├── Invite team       →  email sent with join code          │
 │  └── Manage users      →  roles: employee / manager / admin  │
 │                                                              │
 │  ┌─────────────────┐    ┌──────────────────────────────┐    │
 │  │ nova_ai (DB)    │    │ nova_ai_confidential (DB)    │    │
 │  │ Public docs     │    │ Confidential docs            │    │
 │  │ All roles       │    │ Manager / Admin only         │    │
 │  └─────────────────┘    └──────────────────────────────┘    │
 │                                                              │
 │  Employee asks a question                                    │
 │  └── 5-Agent pipeline runs                                   │
 │      ├── Security   → RBAC, Lakera Guard                     │
 │      ├── Retrieval  → MongoDB Vector Search (scoped)         │
 │      ├── Validation → Confidence score, HITL trigger         │
 │      ├── Tools      → Google Workspace plugins               │
 │      └── GPT-4      → Final answer                          │
 └──────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | OpenAI GPT-4 |
| Embeddings | `text-embedding-3-small` (1536-dim) |
| Vector Search | MongoDB Atlas Vector Search |
| Database | MongoDB Atlas |
| Auth | Nova JWT (HS256) — join code + email + password |
| API | FastAPI + Uvicorn |
| Security | Lakera Guard (prompt injection, PII, jailbreak) |
| Graph RAG | NetworkX (entity-relationship reasoning) |
| HITL | Custom human-in-the-loop escalation |
| Email | SMTP — invite emails from admin's own Gmail |
| Plugins | Google Drive, Docs, Sheets, Gmail, Calendar, Meet |

---

## Security Model

### Dual Database Isolation

```
MongoDB Atlas
│
├── nova_ai                    (Public)
│   ├── companies
│   ├── users
│   ├── audit_logs
│   └── knowledge_vectors      ← all roles can search here
│
└── nova_ai_confidential       (Confidential)
    └── knowledge_vectors      ← manager / admin only
```

Employee code **never connects** to `nova_ai_confidential`. It is not filtered — it is literally never queried.

### Role Access

| Role | Public DB | Confidential DB | Dashboard |
|:---|:---:|:---:|:---:|
| `employee` | ✅ | ✗ | ✗ |
| `team_lead` | ✅ | ✅ | ✗ |
| `manager` | ✅ | ✅ | ✗ |
| `admin` | ✅ | ✅ | ✅ |

### Authentication

All company users log in with: **join code + email + password → Nova JWT**

No third-party SSO required for company users. Clerk is used only for developer/platform tooling.

---

## Getting Started

### 1 — Clone & Install

```bash
git clone https://github.com/SAGARRAMBADE21/Nova-AI-.git QueryMind
cd QueryMind/Backend
pip install -r requirements.txt
```

### 2 — Environment Setup

```bash
cp .env.example .env
```

Fill in the required values:

```env
# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# MongoDB Atlas
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster0.xxxxx.mongodb.net/
MONGODB_DB_NAME=nova_ai
MONGODB_CONFIDENTIAL_DB_NAME=nova_ai_confidential

# JWT Secret (generate with the command below)
NOVA_JWT_SECRET=<your-secret>
```

Generate a secure JWT secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3 — MongoDB Vector Search Index

In Atlas → Atlas Search → Create Index → **Vector Search** → JSON Editor

Apply this to `knowledge_vectors` in **both** `nova_ai` and `nova_ai_confidential`:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    { "type": "filter", "path": "tenant_id" },
    { "type": "filter", "path": "db_type" }
  ]
}
```

> Index name must be exactly: `vector_index`

### 4 — Run

```bash
python api/server.py
```

Open `http://localhost:8000/docs` for the interactive API explorer.

---

## API Reference

| Method | Endpoint | Auth | Description |
|:---|:---|:---:|:---|
| `POST` | `/onboard` | public | Create company workspace |
| `POST` | `/register` | public | First-time password setup |
| `POST` | `/join` | public | Login → returns JWT |
| `GET` | `/health` | public | Server health check |
| `POST` | `/chat` | JWT | Ask a question |
| `POST` | `/ingest` | admin | Upload document to public or confidential DB |
| `POST` | `/invite-user` | admin | Add user + send invite email |
| `POST` | `/email-config` | admin | Set Gmail for sending invite emails |
| `GET` | `/users` | admin | List all workspace users |
| `GET` | `/metrics` | JWT | LLMOps performance stats |

---

## Complete Workflow

### Step 1 — Company owner signs up
```bash
curl -X POST http://localhost:8000/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "company_name":   "Acme Corp",
    "admin_email":    "admin@acme.com",
    "admin_password": "SecurePass123"
  }'
```
```json
{
  "join_code": "ACMEXK7P12",
  "tenant_id": "tenant_a1b2c3d4...",
  "message":   "Workspace created! Share the join code with your team."
}
```

### Step 2 — Admin configures Gmail for invites
```bash
curl -X POST http://localhost:8000/email-config \
  -H "Authorization: Bearer <admin_jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_email":    "admin@gmail.com",
    "sender_password": "abcd efgh ijkl mnop"
  }'
```

> Get an App Password at `myaccount.google.com → Security → App Passwords`

### Step 3 — Admin invites an employee (email sent automatically)
```bash
curl -X POST http://localhost:8000/invite-user \
  -H "Authorization: Bearer <admin_jwt>" \
  -H "Content-Type: application/json" \
  -d '{ "email": "john@acme.com", "role": "employee" }'
```

John receives an email with the join code and registration steps.

### Step 4 — John registers
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "join_code": "ACMEXK7P12",
    "email":     "john@acme.com",
    "password":  "MyPassword123"
  }'
```

### Step 5 — John logs in
```bash
curl -X POST http://localhost:8000/join \
  -H "Content-Type: application/json" \
  -d '{
    "join_code": "ACMEXK7P12",
    "email":     "john@acme.com",
    "password":  "MyPassword123"
  }'
```
```json
{ "token": "eyJhbGci...", "role": "employee" }
```

### Step 6 — John chats with ARIA
```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer <john_jwt>" \
  -H "Content-Type: application/json" \
  -d '{ "prompt": "What is our annual leave policy?" }'
```

---

## Project Structure

``` 
Backend/
│
├── api/
│   └── server.py              API endpoints + unified auth dependency
│
├── db/
│   └── mongodb.py             TenantManager · TenantVectorStore
│                              Password hashing · Email config encryption
│
├── security/
│   ├── nova_jwt.py            Employee JWT (HS256)
│   ├── clerk_auth.py          Clerk JWT (developer-only)
│   ├── rbac.py                Role → DB scope mapping
│   └── lakera_guard.py        Prompt injection · PII protection
│
├── core/
│   ├── rag.py                 SelfCorrectingRAG (dual-DB aware)
│   ├── hitl.py                Human-in-the-loop controller
│   └── web_scraper.py         Web fallback retrieval
│
├── agents/
│   └── multi_agent.py         5-agent orchestration pipeline
│
├── data/
│   └── ingestion.py           File parsing · Dual-DB routing
│
├── plugins/
│   ├── registry.py
│   ├── gmail.py
│   ├── google_drive.py
│   ├── google_docs.py
│   ├── google_sheets.py
│   ├── google_calendar.py
│   └── google_meet.py
│
├── utils/
│   ├── email_sender.py        SMTP invite emails (admin's Gmail)
│   └── llmops.py              Interaction logging · Metrics
│
├── main.py                    Core assistant class · CLI demo
├── requirements.txt
└── .env.example
```

---

## Environment Variables

| Variable | Required | Description |
|:---|:---:|:---|
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `OPENAI_MODEL` | ✅ | LLM model (default: `gpt-4`) |
| `OPENAI_EMBEDDING_MODEL` | ✅ | Embedding model |
| `MONGODB_URI` | ✅ | Atlas connection string |
| `MONGODB_DB_NAME` | ✅ | Public DB name |
| `MONGODB_CONFIDENTIAL_DB_NAME` | ✅ | Confidential DB name |
| `NOVA_JWT_SECRET` | ✅ | JWT signing secret |
| `CLERK_PUBLISHABLE_KEY` | dev | Clerk (developer use only) |
| `CLERK_SECRET_KEY` | dev | Clerk (developer use only) |
| `CLERK_JWKS_URL` | dev | Clerk JWKS URL |
| `LAKERA_API_KEY` | optional | Lakera Guard API key |
| `LOG_LEVEL` | optional | Logging level (default: `INFO`) |
| `DEV_TENANT_ID` | dev | Mock tenant for local testing |

---

## Roadmap

- [ ] Next.js Admin Dashboard — document upload, user management, email config UI
- [ ] Employee Chat Interface — responsive frontend
- [ ] Slack / Notion plugin integration
- [ ] OpenTelemetry + Grafana metrics dashboard
- [ ] Document version control + re-ingestion
- [ ] Multi-language support

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
<br />
Built with ❤️ for enterprise teams who deserve better AI tools.
<br /><br />
</div>
