# ARIA — Enterprise AI Assistant
### Adaptive Retrieval Intelligence Assistant
**Secure · Agentic · RAG-Powered · Production-Ready**

---

## Overview

ARIA is a production-grade enterprise AI assistant built for internal operations.
It combines **Retrieval-Augmented Generation (RAG)**, a **5-agent pipeline**, **real-time tool integrations**, and a **multi-layer security architecture** to deliver accurate, auditable, and safe AI assistance across your organisation.

> **Powered by:** OpenAI GPT-4 · ChromaDB · LangChain · FastAPI · Lakera Guard

---

## Project Structure

```
enterprise_ai/
│
├── main.py                        # Main assistant entry point + CLI
├── requirements.txt               # All Python dependencies
├── .env.example                   # Environment variable template
├── README.md                      # This file
│
├── security/
│   ├── lakera_guard.py            # 3-checkpoint AI firewall (input / doc / output)
│   └── rbac.py                    # Role-based access control (Employee → Admin)
│
├── core/
│   ├── rag.py                     # Vector RAG + Graph RAG + Self-Correcting RAG
│   ├── hitl.py                    # Human-in-the-Loop (3 escalation levels)
│   └── web_scraper.py             # Real-time web scraping pipeline
│
├── agents/
│   └── multi_agent.py             # 5-agent orchestration system
│
├── data/
│   └── ingestion.py               # Real-time admin document ingestion
│
├── plugins/
│   ├── base.py                    # BasePlugin, PluginResult, @with_retry
│   ├── registry.py                # PluginRegistry (health checks, discovery)
│   ├── plugin_system.py           # Backward-compatibility shim
│   ├── google_drive.py            # Google Drive plugin
│   ├── google_docs.py             # Google Docs plugin
│   ├── google_sheets.py           # Google Sheets plugin
│   ├── google_calendar.py         # Google Calendar plugin
│   ├── gmail.py                   # Gmail plugin
│   ├── google_meet.py             # Google Meet plugin
│   ├── slack.py                   # Slack plugin
│   ├── notion.py                  # Notion plugin
│   └── grafana.py                 # Grafana plugin
│
├── utils/
│   └── llmops.py                  # Observability, PII-safe logging, metrics
│
└── api/
    └── server.py                  # FastAPI REST server (chat / ingest / metrics)
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# → Fill in your API keys in .env

# 3. Run CLI (interactive mode)
python main.py

# 4. Run REST API server
python api/server.py
# → API available at http://localhost:8000
```

---

## Environment Variables

| Variable                  | Description                              | Required |
|---------------------------|------------------------------------------|----------|
| `OPENAI_API_KEY`          | OpenAI API key                           | ✅ Yes   |
| `OPENAI_MODEL`            | Model to use (default: `gpt-4`)          | Optional |
| `LAKERA_API_KEY`          | Lakera Guard API key                     | Optional |
| `LAKERA_PROJECT_ID`       | Lakera project ID                        | Optional |
| `CHROMA_PERSIST_DIR`      | Path to ChromaDB storage                 | Optional |
| `GOOGLE_CREDENTIALS_FILE` | Google OAuth credentials file path       | Optional |
| `GOOGLE_TOKEN_FILE`       | Google OAuth token file path             | Optional |
| `SLACK_BOT_TOKEN`         | Slack Bot token                          | Optional |
| `NOTION_API_KEY`          | Notion integration API key               | Optional |
| `GRAFANA_URL`             | Grafana instance URL                     | Optional |
| `GRAFANA_API_KEY`         | Grafana API key                          | Optional |
| `LOG_LEVEL`               | Logging level (default: `INFO`)          | Optional |
| `LOG_FILE`                | Log file path                            | Optional |
| `METRICS_PORT`            | Prometheus metrics port (default: 8001)  | Optional |
| `HITL_CONFIDENCE_THRESHOLD` | HITL trigger threshold (default: 0.4) | Optional |
| `HITL_SLA_MINUTES`        | HITL response SLA in minutes             | Optional |
| `ADMIN_EMAIL`             | Admin email for escalations              | Optional |

---

## API Endpoints

```bash
# Send a chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is our Q3 revenue?", "user_id": "user_001", "user_role": "employee"}'

# Admin: ingest a document into the knowledge base
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"file_path": "./data/report.pdf", "category": "finance", "uploaded_by": "admin"}'

# View LLMOps metrics
curl http://localhost:8000/metrics

# Health check
curl http://localhost:8000/health
```

---

## Full Request Pipeline

```
User Prompt
    ↓
[1] Lakera Guard — INPUT SCAN       (injection / jailbreak / PII detection)
    ↓ clean
[2] Security Agent — RBAC CHECK     (role-based access enforcement)
    ↓ authorised
[3] Retrieval Agent — RAG           (Vector RAG + Graph RAG + web scraping)
    ↓
[4] Self-Correcting RAG             (relevance scoring / conflict detection / confidence)
    ↓
[5] Lakera Guard — DOCUMENT SCAN    (poisoned chunk detection)
    ↓ clean
[6] Validation Agent                (cross-checks results, triggers HITL if needed)
    ↓
[7] Tool Agent                      (detects intent, queues plugin actions)
    ↓
[8] HITL Gate                       (low confidence or high-risk → human reviewer)
    ↓ approved
[9] LLM — OpenAI GPT-4              (structured response generation via ARIA prompt)
    ↓
[10] Lakera Guard — OUTPUT SCAN     (leakage / PII / hallucination detection)
    ↓ safe
[11] Plugin Execution               (tools run silently or request confirmation)
    ↓
[12] LLMOps Logger                  (interaction log: query, agents, tools, security, latency)
    ↓
Final Response → User
```

---

## Security Architecture

| Layer              | Component      | What It Does                                      |
|--------------------|----------------|---------------------------------------------------|
| Input firewall     | Lakera Guard   | Blocks prompt injections, jailbreaks, PII leakage |
| Access control     | RBAC           | Role-based data category permissions              |
| Document firewall  | Lakera Guard   | Removes poisoned or malicious RAG chunks          |
| Output firewall    | Lakera Guard   | Prevents data leakage and PII in responses        |
| Audit trail        | LLMOps         | Full PII-stripped interaction log (JSONL)         |
| Escalation gate    | HITL           | Human review for low-confidence / high-risk tasks |

### RBAC Roles

| Role       | Access Level                                              |
|------------|-----------------------------------------------------------|
| `employee` | General knowledge, public policies, self-service tasks   |
| `manager`  | Team data, reports, scheduling, performance data         |
| `admin`    | Full access including sensitive financial and HR data    |

---

## Agents

| Agent               | Responsibility                                              |
|---------------------|-------------------------------------------------------------|
| `OrchestratorAgent` | Coordinates all agents, assembles the final response        |
| `SecurityAgent`     | Enforces RBAC before any retrieval or action occurs         |
| `RetrievalAgent`    | Runs Vector RAG + Graph RAG + web scraping fallback         |
| `ValidationAgent`   | Cross-checks data, detects conflicts, triggers HITL         |
| `ToolAgent`         | Detects tool intent from queries, queues plugin actions     |

---

## Plugins

Each plugin lives in its own file under `plugins/` and supports:
- ✅ Retry logic with exponential backoff (`@with_retry`)
- ✅ Input validation on all required parameters
- ✅ Health check (`health_check()`)
- ✅ Action discovery (`list_actions()`)
- ✅ Structured error codes (`NOT_CONNECTED`, `INVALID_PARAMS`, etc.)

| Plugin            | File                    | Actions                                                                 |
|-------------------|-------------------------|-------------------------------------------------------------------------|
| Google Drive      | `google_drive.py`       | list_files, search_files, upload_file, download_file, delete_file, share_file |
| Google Docs       | `google_docs.py`        | create_document, get_document, append_content, edit_document, share_document |
| Google Sheets     | `google_sheets.py`      | create_spreadsheet, read_data, push_data, append_row, clear_range      |
| Google Calendar   | `google_calendar.py`    | list_events, create_event, update_event, delete_event, set_reminder    |
| Gmail             | `gmail.py`              | send_email, draft_email, search_emails, read_email, reply_email, create_label |
| Google Meet       | `google_meet.py`        | create_meeting, schedule_call (real Meet links via Calendar API)        |
| Slack             | `slack.py`              | send_message, list_channels, upload_file, reply_to_thread, get_channel_history |
| Notion            | `notion.py`             | create_page, get_page, search_pages, update_page, append_blocks        |
| Grafana           | `grafana.py`            | push_metrics, list_dashboards, get_dashboard, create_annotation         |

### Plugin Registry Usage

```python
from plugins import PluginRegistry

registry = PluginRegistry()

# List all plugins
registry.list_plugins()

# List actions for a plugin
registry.list_actions("slack")

# Execute an action
result = registry.execute("slack", "send_message", {
    "channel": "#general",
    "message": "Deployment complete ✅"
})

# Health check all plugins
registry.health_report()
```

---

## LLMOps & Observability

All interactions are automatically logged to `logs/interactions.jsonl` with:
- Interaction ID, user ID, session ID
- Query and response (PII-stripped)
- Confidence level and sources used
- Tool actions executed
- Security events triggered
- Latency (ms) and token count
- HITL trigger flag

**Metrics tracked:**
- Total queries, avg latency, total tokens
- Tool invocations, security blocks, HITL requests, errors

---

## HITL (Human-in-the-Loop)

ARIA automatically escalates to a human reviewer when:
- Retrieval confidence is **LOW**
- The query contains high-risk keywords (`salary`, `legal`, `delete`, `bulk`, `financial`)
- A tool action is irreversible and affects multiple users
- The user explicitly requests escalation

**Escalation levels:**
| Level     | Trigger                        | SLA              |
|-----------|--------------------------------|------------------|
| `LOW`     | Low confidence retrieval       | 30 min (default) |
| `MEDIUM`  | Sensitive data category access | 15 min           |
| `HIGH`    | High-risk irreversible actions | Immediate        |

---

## Data Ingestion

ARIA supports real-time document ingestion into the knowledge base:

| Format | Support |
|--------|---------|
| PDF    | ✅ via PyPDF2   |
| DOCX   | ✅ via python-docx |
| XLSX   | ✅ via openpyxl |
| CSV    | ✅ native       |
| TXT    | ✅ native       |
| JSON   | ✅ native       |
| XML    | ✅ native       |
| URLs   | ✅ via web scraper |

---

## Contributing

1. Add a new plugin → create `plugins/<name>.py` extending `BasePlugin`
2. Register it in `plugins/registry.py` → `_register_all()`
3. Add trigger keywords in `agents/multi_agent.py` → `ToolAgent.TOOL_MAP`
4. Update `.env.example` with any new credentials needed
