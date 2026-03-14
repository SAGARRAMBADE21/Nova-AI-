# Nova AI — Enterprise AI Assistant (ARIA)

> **Adaptive Retrieval Intelligence Assistant** — A secure, multi-tenant enterprise AI platform powered by GPT-4, MongoDB Atlas Vector Search, and Clerk authentication.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb)](https://cloud.mongodb.com)
[![Clerk](https://img.shields.io/badge/Auth-Clerk-6C47FF?logo=clerk)](https://clerk.com)
[![OpenAI](https://img.shields.io/badge/GPT--4-OpenAI-412991?logo=openai)](https://openai.com)

---

## 🌟 What is Nova AI?

Nova AI is a **production-ready enterprise AI assistant** that gives companies their own private, isolated AI workspace. Each company's data is completely separated from others. Employees get an AI assistant that knows their company's internal knowledge — and nothing else.

**Key differentiator:** Unlike generic AI tools (ChatGPT, Copilot), Nova AI only answers from **your company's own documents**, with strict role-based access so sensitive data stays protected.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        COMPANY WORKSPACE                        │
│                    (Clerk Organization)                         │
├─────────────────┬───────────────────────────────────────────────┤
│   EMPLOYEES     │   MANAGERS / TEAM LEADS / ADMINS              │
│                 │                                               │
│  ┌──────────┐   │   ┌──────────────────────────────────┐        │
│  │  /chat   │   │   │  /chat  /ingest  /invite-user    │        │
│  └────┬─────┘   │   └──────────────┬───────────────────┘        │
│       │         │                  │                            │
│  ┌────▼─────────▼──────────────────▼───────────────────┐       │
│  │              FastAPI + Clerk JWT                      │       │
│  │         (tenant_id + role extracted)                  │       │
│  └────────────────────────┬──────────────────────────────┘      │
│                           │                                     │
│  ┌────────────────────────▼──────────────────────────────┐      │
│  │              5-Agent Pipeline                          │      │
│  │  Security → Retrieval → Validation → Tool → Response  │      │
│  └──────┬─────────────────────────────────────┬──────────┘      │
│         │                                     │                 │
│  ┌──────▼──────────┐              ┌────────────▼────────┐       │
│  │  nova_ai (DB)   │              │ nova_ai_confidential│       │
│  │  Public Docs    │              │   Private Docs      │       │
│  │  (All roles)    │              │  (Manager+ only)    │       │
│  └─────────────────┘              └─────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **LLM** | OpenAI GPT-4 | Natural language responses |
| **Embeddings** | `text-embedding-3-small` | 1536-dim semantic vectors |
| **Vector DB** | MongoDB Atlas Vector Search | Semantic document retrieval |
| **Metadata DB** | MongoDB Atlas | Companies, users, audit logs |
| **Auth** | Clerk + JWT (RS256) | Multi-tenant SSO, organizations, roles |
| **API** | FastAPI + Uvicorn | REST endpoints |
| **Security** | Lakera Guard | Prompt injection, PII, jailbreak protection |
| **Graph RAG** | NetworkX | Entity-relationship cross-document reasoning |
| **HITL** | Custom Controller | Human-in-the-loop escalation |
| **Plugins** | Google Workspace | Drive, Docs, Sheets, Gmail, Calendar, Meet |

---

## 🔐 Multi-Tenant Architecture

Every company gets a **fully isolated workspace**:

- **Clerk Organization** = Company workspace (unique `org_id` = `tenant_id`)
- **Join Code** = Unique code employees use to access their company workspace
- **Dual MongoDB Databases** = True physical data separation

### Dual Database Isolation

```
nova_ai                   ← Regular database
├── companies             (workspace metadata)
├── users                 (employee records + roles)
├── audit_logs            (compliance trail)
└── knowledge_vectors     (public documents — all roles)

nova_ai_confidential      ← Confidential database
└── knowledge_vectors     (private documents — managers+ only)
```

### Role-Based Access Control (RBAC)

| Role | Public DB (`nova_ai`) | Confidential DB (`nova_ai_confidential`) |
|---|---|---|
| `employee` | ✅ Full access | ❌ Never queried |
| `team_lead` | ✅ Full access | ✅ Full access |
| `manager` | ✅ Full access | ✅ Full access |
| `admin` | ✅ Full access | ✅ Full access |

> **Security guarantee:** An employee request physically never touches `nova_ai_confidential`. It is not filtered — it is simply never queried.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB Atlas account (free tier works)
- Clerk account (free tier works)
- OpenAI API key

### 1. Clone & Install

```bash
git clone https://github.com/SAGARRAMBADE21/Nova-AI-.git
cd Nova-AI-/enterprise_ai
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:
```env
# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# MongoDB Atlas
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster0.xxxxx.mongodb.net/
MONGODB_DB_NAME=nova_ai
MONGODB_CONFIDENTIAL_DB_NAME=nova_ai_confidential

# Clerk
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_JWKS_URL=https://your-app.clerk.accounts.dev/.well-known/jwks.json
```

### 3. MongoDB Atlas Setup

**Step 1** — Create cluster (M0 Free Tier) at [cloud.mongodb.com](https://cloud.mongodb.com)

**Step 2** — Create Vector Search index on **both** databases:

Go to Atlas → Atlas Search → Create Index → **Vector Search** → JSON Editor

Collection: `knowledge_vectors` (do this for both `nova_ai` **and** `nova_ai_confidential`)

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "tenant_id"
    },
    {
      "type": "filter",
      "path": "db_type"
    }
  ]
}
```

Index name: `vector_index` *(exact — the code looks for this)*

### 4. Clerk Setup

1. Go to [clerk.com](https://clerk.com) → Create Application
2. Enable **Organizations** (sidebar → Organizations → toggle ON)
3. Copy: Publishable Key, Secret Key, JWKS URL

### 5. Run

**API Server:**
```bash
python api/server.py
# → http://localhost:8000/docs
```

**CLI Demo:**
```bash
python main.py
```

---

## 📡 API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/onboard` | 🔓 Public | Create company workspace |
| `GET` | `/health` | 🔓 Public | Health check |
| `POST` | `/chat` | 🔒 JWT | Ask ARIA a question |
| `POST` | `/ingest` | 🔒 Admin only | Upload document to knowledge base |
| `POST` | `/invite-user` | 🔒 Admin only | Add employee with role |
| `GET` | `/users` | 🔒 Admin only | List all workspace users |
| `GET` | `/metrics` | 🔒 JWT | LLMOps performance metrics |

### Onboard a Company

```bash
curl -X POST http://localhost:8000/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Acme Corp",
    "admin_email": "admin@acme.com",
    "tenant_id": "org_clerk_abc123"
  }'
```

Response:
```json
{
  "tenant_id": "org_clerk_abc123",
  "join_code": "ACMEXK7P12",
  "company_name": "Acme Corp"
}
```

### Chat with ARIA

```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer <clerk_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is our annual leave policy?"}'
```

### Ingest a Document (Admin)

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Authorization: Bearer <clerk_admin_jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "./data/hr_policy.pdf",
    "category": "hr",
    "db_type": "public"
  }'
```

Use `"db_type": "private"` to ingest into the confidential database.

---

## 🤖 5-Agent Pipeline

Every request goes through a 5-stage agent pipeline:

```
User Query
    │
    ▼
┌─────────────────┐
│ SecurityAgent   │  ← RBAC check: resolves allowed_db_types from role
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│ RetrievalAgent  │  ← MongoDB Atlas Vector Search (tenant + role scoped)
│                 │    + NetworkX Knowledge Graph
│                 │    + Web scraping fallback
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│ValidationAgent  │  ← Confidence scoring, conflict detection, HITL trigger
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│  ToolAgent      │  ← Detects plugin actions (email, calendar, Drive, etc.)
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│    GPT-4        │  ← Final response with RAG context injected
└─────────────────┘
```

---

## 📁 Project Structure

```
enterprise_ai/
├── main.py                    # Core assistant class + CLI demo
├── requirements.txt
├── .env.example
│
├── api/
│   └── server.py              # FastAPI REST server + JWT middleware
│
├── db/
│   └── mongodb.py             # TenantManager + TenantVectorStore (Atlas)
│
├── security/
│   ├── clerk_auth.py          # Clerk JWT verification (FastAPI dependency)
│   ├── rbac.py                # Role → db_type mapping
│   └── lakera_guard.py        # Prompt injection + PII protection
│
├── core/
│   ├── rag.py                 # SelfCorrectingRAG + KnowledgeGraph
│   ├── hitl.py                # Human-in-the-loop controller
│   └── web_scraper.py         # Web scraping fallback
│
├── agents/
│   └── multi_agent.py         # 5-agent orchestration pipeline
│
├── data/
│   └── ingestion.py           # File parsing + dual-DB routing
│
├── plugins/
│   ├── registry.py            # Plugin registry
│   ├── gmail.py               # Gmail integration
│   ├── google_drive.py        # Google Drive integration
│   ├── google_docs.py         # Google Docs integration
│   ├── google_sheets.py       # Google Sheets integration
│   ├── google_calendar.py     # Google Calendar integration
│   └── google_meet.py         # Google Meet integration
│
├── utils/
│   └── llmops.py              # Interaction logging + metrics
│
└── credentials/
    └── google_credentials.json # Google OAuth (gitignored)
```

---

## 🔒 Security Features

| Feature | Implementation |
|---|---|
| **JWT Verification** | Clerk RS256 JWT — verified on every request |
| **Tenant Isolation** | All DB queries filtered by `tenant_id` from JWT |
| **Dual DB** | `nova_ai` (public) + `nova_ai_confidential` (private) — physically separate |
| **RBAC** | Role resolved from Clerk org role → db access scope |
| **Prompt Injection** | Lakera Guard scans all inputs |
| **PII Protection** | Lakera Guard strips PII from logs and outputs |
| **Output Scanning** | Lakera Guard validates LLM output before sending |
| **Audit Logs** | Every interaction logged to MongoDB with tenant scope |
| **HITL** | Low-confidence answers escalated to human review |

---

## 🗺️ Roadmap

- [ ] Next.js frontend with Clerk authentication
- [ ] Admin dashboard (document upload UI, user management)
- [ ] Employee chat interface
- [ ] Slack / Notion plugin integration
- [ ] OpenTelemetry + Grafana metrics dashboard
- [ ] Document version control
- [ ] Multi-language support

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `OPENAI_MODEL` | ✅ | LLM model (default: `gpt-4`) |
| `OPENAI_EMBEDDING_MODEL` | ✅ | Embedding model (default: `text-embedding-3-small`) |
| `MONGODB_URI` | ✅ | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | ✅ | Public database name (default: `nova_ai`) |
| `MONGODB_CONFIDENTIAL_DB_NAME` | ✅ | Confidential database name (default: `nova_ai_confidential`) |
| `CLERK_PUBLISHABLE_KEY` | ✅ | Clerk publishable key |
| `CLERK_SECRET_KEY` | ✅ | Clerk secret key |
| `CLERK_JWKS_URL` | ✅ | Clerk JWKS endpoint for JWT verification |
| `DEV_TENANT_ID` | Dev only | Mock tenant for local dev (bypasses Clerk) |
| `LAKERA_API_KEY` | Optional | Lakera Guard API key |
| `GOOGLE_CREDENTIALS_FILE` | Optional | Google OAuth credentials path |
| `LOG_LEVEL` | Optional | Logging level (default: `INFO`) |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <strong>Built with ❤️ for enterprise teams who deserve better AI tools.</strong>
</div>
