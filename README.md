# Nova AI — Enterprise AI Assistant (ARIA)

> **Adaptive Retrieval Intelligence Assistant** — A secure, multi-tenant enterprise AI platform powered by GPT-4, MongoDB Atlas Vector Search, and role-based password authentication.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb)](https://cloud.mongodb.com)
[![OpenAI](https://img.shields.io/badge/GPT--4-OpenAI-412991?style=for-the-badge&logo=openai)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 🌟 What is Nova AI?

Nova AI is a **production-ready enterprise AI assistant** that gives companies their own private, isolated AI workspace. Each company's data is completely separated from others. Employees get an AI assistant that answers only from **their company's own documents** — with strict role-based access so sensitive data stays protected.

**Key differentiator:** Unlike generic AI tools (ChatGPT, Copilot), Nova AI is scoped entirely to your company. Confidential documents are physically stored in a separate database — employees can never access them.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         COMPANY WORKSPACE                            │
├──────────────────────┬───────────────────────────────────────────────┤
│   EMPLOYEE           │   MANAGER / TEAM LEAD / ADMIN                 │
│                      │                                               │
│  join_code+email+pw  │   join_code+email+pw  (Nova JWT)              │
│         │            │              │                                 │
│  ┌──────▼────────────▼──────────────▼──────────────────────┐        │
│  │        FastAPI  —  Nova JWT auth (HS256)                 │        │
│  │       (tenant_id + role extracted from token)            │        │
│  └───────────────────────────┬──────────────────────────────┘        │
│                              │                                        │
│  ┌───────────────────────────▼──────────────────────────────┐        │
│  │              5-Agent Pipeline                             │        │
│  │  Security → Retrieval → Validation → Tool → GPT-4        │        │
│  └──────┬────────────────────────────────────────┬──────────┘        │
│         │                                        │                   │
│  ┌──────▼──────────┐                  ┌──────────▼────────────┐      │
│  │  nova_ai (DB)   │                  │ nova_ai_confidential  │      │
│  │  Public Docs    │                  │   Private Docs        │      │
│  │  (All roles)    │                  │  (Manager+ only)      │      │
│  └─────────────────┘                  └───────────────────────┘      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **LLM** | OpenAI GPT-4 | Natural language responses |
| **Embeddings** | `text-embedding-3-small` | 1536-dim semantic vectors |
| **Vector DB** | MongoDB Atlas Vector Search | Semantic document retrieval |
| **Metadata DB** | MongoDB Atlas | Companies, users, audit logs |
| **Auth** | Nova JWT (HS256) | Password-based login with join code |
| **API** | FastAPI + Uvicorn | REST endpoints |
| **Security** | Lakera Guard | Prompt injection, PII, jailbreak protection |
| **Graph RAG** | NetworkX | Entity-relationship cross-document reasoning |
| **HITL** | Custom Controller | Human-in-the-loop escalation |
| **Email** | SMTP (Gmail) | Invite emails from admin's own Gmail |
| **Plugins** | Google Workspace | Drive, Docs, Sheets, Gmail, Calendar, Meet |

---

## 🔐 Multi-Tenant Architecture

Every company gets a **fully isolated workspace**:

- **Auto-generated `tenant_id`** = Company workspace (UUID, no external service needed)
- **Join Code** = Unique code employees use to register + login
- **Dual MongoDB Databases** = True physical data separation

### Dual Database Isolation

```
nova_ai                   ← Regular database
├── companies             (workspace metadata + email config)
├── users                 (employee records, roles, hashed passwords)
├── audit_logs            (compliance trail)
└── knowledge_vectors     (public documents — all roles)

nova_ai_confidential      ← Confidential database
└── knowledge_vectors     (private documents — managers+ only)
```

> **Security guarantee:** An employee request physically **never touches** `nova_ai_confidential`. It is not filtered — it is simply never queried.

### Role-Based Access Control (RBAC)

| Role | Public DB | Confidential DB | Admin Actions |
|---|---|---|---|
| `employee` | ✅ | ❌ Never queried | ❌ |
| `team_lead` | ✅ | ✅ | ❌ |
| `manager` | ✅ | ✅ | ❌ |
| `admin` | ✅ | ✅ | ✅ invite, ingest, config |

### Authentication

| User type | Login method | Token |
|---|---|---|
| **Admin** | `join_code + email + password` | Nova JWT (12h) |
| **Manager / Team Lead** | `join_code + email + password` | Nova JWT (12h) |
| **Employee** | `join_code + email + password` | Nova JWT (12h) |
| **Developer** | Clerk (internal only) | Clerk JWT |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB Atlas account (free M0 tier works)
- OpenAI API key

### 1. Clone & Install

```bash
git clone https://github.com/SAGARRAMBADE21/Nova-AI-.git
cd Nova-AI-/enterprise_ai
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Fill in your values
```

Minimum required:
```env
OPENAI_API_KEY=sk-proj-...
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster0.xxxxx.mongodb.net/
NOVA_JWT_SECRET=<run: python -c "import secrets; print(secrets.token_hex(32))">
```

### 3. MongoDB Atlas — Vector Search Index

Create this index on `knowledge_vectors` in **both** `nova_ai` and `nova_ai_confidential`:

```json
{
  "fields": [
    { "type": "vector", "path": "embedding", "numDimensions": 1536, "similarity": "cosine" },
    { "type": "filter", "path": "tenant_id" },
    { "type": "filter", "path": "db_type" }
  ]
}
```

Index name: `vector_index`

### 4. Run

```bash
python api/server.py
# → http://localhost:8000/docs
```

---

## 📡 API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/onboard` | 🔓 Public | Company owner creates workspace + admin account |
| `POST` | `/register` | 🔓 Public | First-time user sets their password |
| `POST` | `/join` | 🔓 Public | Login → returns Nova JWT |
| `GET` | `/health` | 🔓 Public | Health check |
| `POST` | `/chat` | 🔒 Nova JWT | Ask ARIA a question |
| `POST` | `/ingest` | 🔒 Admin JWT | Upload document (public or confidential) |
| `POST` | `/invite-user` | 🔒 Admin JWT | Add employee + send invite email |
| `POST` | `/email-config` | 🔒 Admin JWT | Set admin Gmail for sending invites |
| `GET` | `/users` | 🔒 Admin JWT | List all workspace users |
| `GET` | `/metrics` | 🔒 Any JWT | LLMOps performance metrics |

### Complete User Flow

**1. Company owner creates workspace:**
```bash
curl -X POST http://localhost:8000/onboard \
  -d '{"company_name":"Acme Corp","admin_email":"admin@acme.com","admin_password":"SecurePass123"}'
# Returns: join_code (e.g. "ACMEXK7P12")
```

**2. Admin configures email (so invites send from their Gmail):**
```bash
curl -X POST http://localhost:8000/email-config \
  -H "Authorization: Bearer <admin_jwt>" \
  -d '{"sender_email":"admin@gmail.com","sender_password":"abcd efgh ijkl mnop"}'
```

**3. Admin invites an employee (sends real email):**
```bash
curl -X POST http://localhost:8000/invite-user \
  -H "Authorization: Bearer <admin_jwt>" \
  -d '{"email":"john@acme.com","role":"employee"}'
# John receives email with join code + registration steps
```

**4. John registers:**
```bash
curl -X POST http://localhost:8000/register \
  -d '{"join_code":"ACMEXK7P12","email":"john@acme.com","password":"MyPass123"}'
```

**5. John logs in:**
```bash
curl -X POST http://localhost:8000/join \
  -d '{"join_code":"ACMEXK7P12","email":"john@acme.com","password":"MyPass123"}'
# Returns: { "token": "eyJ..." }
```

**6. John chats with ARIA:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer <john_jwt>" \
  -d '{"prompt":"What is our annual leave policy?"}'
```

---

## 🤖 5-Agent Pipeline

```
User Query
    │
    ▼
┌─────────────────┐
│ SecurityAgent   │  ← RBAC: resolves allowed_db_types from role
└────────┬────────┘
         ▼
┌─────────────────┐
│ RetrievalAgent  │  ← MongoDB Atlas Vector Search (tenant + role scoped)
│                 │    + NetworkX Knowledge Graph + Web fallback
└────────┬────────┘
         ▼
┌─────────────────┐
│ValidationAgent  │  ← Confidence scoring, conflict detection, HITL trigger
└────────┬────────┘
         ▼
┌─────────────────┐
│  ToolAgent      │  ← Detects plugin actions (email, calendar, Drive...)
└────────┬────────┘
         ▼
┌─────────────────┐
│    GPT-4        │  ← Final answer with RAG context injected
└─────────────────┘
```

---

## 📁 Project Structure

```
enterprise_ai/
├── main.py                    # Core assistant + CLI
├── requirements.txt
├── .env.example
│
├── api/
│   └── server.py              # FastAPI — all endpoints
│
├── db/
│   └── mongodb.py             # TenantManager + TenantVectorStore
│                              # (password hashing, email config encryption)
│
├── security/
│   ├── nova_jwt.py            # Employee JWT (HS256, join code flow)
│   ├── clerk_auth.py          # Clerk JWT (developer-only)
│   ├── rbac.py                # Role → db_type mapping
│   └── lakera_guard.py        # Prompt injection + PII protection
│
├── core/
│   ├── rag.py                 # SelfCorrectingRAG (dual DB aware)
│   ├── hitl.py                # Human-in-the-loop controller
│   └── web_scraper.py
│
├── agents/
│   └── multi_agent.py         # 5-agent orchestration
│
├── data/
│   └── ingestion.py           # File parsing + dual-DB routing
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
└── utils/
    ├── email_sender.py        # SMTP invite emails (from admin's Gmail)
    └── llmops.py              # Interaction logging + metrics
```

---

## 🔒 Security Features

| Feature | Implementation |
|---|---|
| **Password Auth** | PBKDF2-SHA256 (200k rounds) — no external libs |
| **JWT** | Nova HS256 JWT (12h expiry) per user session |
| **Tenant Isolation** | All DB queries filtered by `tenant_id` |
| **Dual DB** | Physical separation — employee code never touches confidential DB |
| **RBAC** | Role in JWT → db scope resolved per request |
| **Email Encryption** | Admin Gmail App Password encrypted with Fernet before storing |
| **Prompt Injection** | Lakera Guard scans all inputs |
| **PII Protection** | Lakera Guard strips PII from logs |
| **Audit Logs** | Every interaction logged to MongoDB (tenant-scoped) |
| **HITL** | Low-confidence answers escalated to human review |

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `OPENAI_MODEL` | ✅ | LLM model (`gpt-4`) |
| `OPENAI_EMBEDDING_MODEL` | ✅ | Embedding model (`text-embedding-3-small`) |
| `MONGODB_URI` | ✅ | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | ✅ | Public DB (default: `nova_ai`) |
| `MONGODB_CONFIDENTIAL_DB_NAME` | ✅ | Confidential DB (default: `nova_ai_confidential`) |
| `NOVA_JWT_SECRET` | ✅ | Secret for signing employee JWTs |
| `CLERK_PUBLISHABLE_KEY` | Dev only | Clerk (developer internal use) |
| `CLERK_SECRET_KEY` | Dev only | Clerk (developer internal use) |
| `CLERK_JWKS_URL` | Dev only | Clerk JWKS URL |
| `LAKERA_API_KEY` | Optional | Lakera Guard prompt injection protection |
| `LOG_LEVEL` | Optional | Logging level (default: `INFO`) |

> **Note:** Email credentials (`EMAIL_USER`, `EMAIL_PASSWORD`) are optional platform fallbacks. Each company admin sets their own Gmail via `POST /email-config` from the dashboard.

---

## 🗺️ Roadmap

- [ ] Next.js Admin Dashboard (document upload, user management, email config)
- [ ] Employee Chat Interface (frontend)
- [ ] Slack / Notion plugin
- [ ] OpenTelemetry + Grafana metrics
- [ ] Document version control
- [ ] Multi-language support

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <strong>Built with ❤️ for enterprise teams who deserve better AI tools.</strong>
</div>
