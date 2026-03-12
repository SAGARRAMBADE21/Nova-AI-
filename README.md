<div align="center">

<h1>ARIA — Nova AI</h1>
<h3>Adaptive Retrieval Intelligence Assistant</h3>

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/OpenAI-GPT--4-412991?style=for-the-badge&logo=openai" />
  <img src="https://img.shields.io/badge/FastAPI-REST%20API-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/ChromaDB-Vector%20DB-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

<p><strong>Secure · Agentic · RAG-Powered · Production-Ready</strong></p>

</div>

---

## Overview

**ARIA (Adaptive Retrieval Intelligence Assistant)** is the core AI engine powering **Nova AI** — a production-grade intelligent assistant built for internal operations. It combines:

- **Retrieval-Augmented Generation (RAG)** — Vector, Graph, and Self-Correcting RAG
- **5-Agent Pipeline** — Orchestrator, Security, Retrieval, Validation & Tool agents
- **Multi-Layer Security** — Lakera Guard AI firewall + RBAC access control
- **9 Live Integrations** — Google Workspace, Slack, Notion, Grafana & more
- **Human-in-the-Loop (HITL)** — Automated escalation for sensitive decisions
- **Full LLMOps Observability** — Interaction logging, metrics, and audit trails

> **Powered by:** OpenAI GPT-4 · ChromaDB · LangChain · FastAPI · Lakera Guard

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/SAGARRAMBADE21/Nova-AI-
cd enterprise_ai_assistant

# 2. Create & activate virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r enterprise_ai/requirements.txt

# 4. Configure environment variables
cp enterprise_ai/.env.example enterprise_ai/.env
# -> Open .env and fill in your API keys

# 5. Run CLI (interactive mode)
python enterprise_ai/main.py

# 6. OR run the REST API server
python enterprise_ai/api/server.py
# -> API available at http://localhost:8000
```

---

## Project Structure

```
enterprise_ai_assistant/
|
+-- README.md                          <- You are here
|
+-- enterprise_ai/                     # Main application package
    +-- main.py                        # CLI entry point + interactive loop
    +-- requirements.txt               # All Python dependencies
    +-- .env.example                   # Environment variable template
    +-- README.md                      # Detailed module-level documentation
    |
    +-- security/
    |   +-- lakera_guard.py            # 3-checkpoint AI firewall (input/doc/output)
    |   +-- rbac.py                    # Role-based access control (Employee -> Admin)
    |
    +-- core/
    |   +-- rag.py                     # Vector RAG + Graph RAG + Self-Correcting RAG
    |   +-- hitl.py                    # Human-in-the-Loop (3 escalation levels)
    |   +-- web_scraper.py             # Real-time web scraping pipeline
    |
    +-- agents/
    |   +-- multi_agent.py             # 5-agent orchestration system
    |
    +-- data/
    |   +-- ingestion.py               # Real-time admin document ingestion
    |
    +-- plugins/
    |   +-- base.py                    # BasePlugin, PluginResult, @with_retry
    |   +-- registry.py                # PluginRegistry (health checks, discovery)
    |   +-- google_drive.py            # Google Drive plugin
    |   +-- google_docs.py             # Google Docs plugin
    |   +-- google_sheets.py           # Google Sheets plugin
    |   +-- google_calendar.py         # Google Calendar plugin
    |   +-- gmail.py                   # Gmail plugin
    |   +-- google_meet.py             # Google Meet plugin
    |   +-- slack.py                   # Slack plugin
    |   +-- notion.py                  # Notion plugin
    |   +-- grafana.py                 # Grafana plugin
    |
    +-- utils/
    |   +-- llmops.py                  # Observability, PII-safe logging, metrics
    |   +-- pdf_generator.py           # PDF documentation generator
    |
    +-- api/
        +-- server.py                  # FastAPI REST server (chat / ingest / metrics)
```

---

## Environment Variables

Copy `enterprise_ai/.env.example` to `enterprise_ai/.env` and configure:

| Variable                    | Description                                      | Required   |
|-----------------------------|--------------------------------------------------|------------|
| `OPENAI_API_KEY`            | OpenAI API key                                   | Yes        |
| `OPENAI_MODEL`              | Model to use (default: `gpt-4`)                  | Optional   |
| `LAKERA_API_KEY`            | Lakera Guard API key                             | Optional   |
| `LAKERA_PROJECT_ID`         | Lakera project ID                                | Optional   |
| `CHROMA_PERSIST_DIR`        | Path to ChromaDB vector storage                  | Optional   |
| `GOOGLE_CREDENTIALS_FILE`   | Google OAuth credentials file path               | Optional   |
| `GOOGLE_TOKEN_FILE`         | Google OAuth token file path                     | Optional   |
| `SLACK_BOT_TOKEN`           | Slack Bot token                                  | Optional   |
| `NOTION_API_KEY`            | Notion integration API key                       | Optional   |
| `GRAFANA_URL`               | Grafana instance URL                             | Optional   |
| `GRAFANA_API_KEY`           | Grafana API key                                  | Optional   |
| `LOG_LEVEL`                 | Logging level (default: `INFO`)                  | Optional   |
| `LOG_FILE`                  | Log file path                                    | Optional   |
| `METRICS_PORT`              | Prometheus metrics port (default: `8001`)        | Optional   |
| `HITL_CONFIDENCE_THRESHOLD` | HITL trigger threshold (default: `0.4`)          | Optional   |
| `HITL_SLA_MINUTES`          | HITL response SLA in minutes                     | Optional   |
| `ADMIN_EMAIL`               | Admin email for escalations                      | Optional   |

---

## API Endpoints

Once the server is running at `http://localhost:8000`:

```bash
# Send a chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is our Q3 revenue?", "user_id": "user_001", "user_role": "employee"}'

# Admin: ingest a document into the knowledge base
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"file_path": "./data/report.pdf", "category": "finance", "uploaded_by": "admin"}'

# Generate a PDF documentation report
curl -X POST http://localhost:8000/generate-pdf

# View LLMOps metrics
curl http://localhost:8000/metrics

# Health check
curl http://localhost:8000/health
```

The API also serves **interactive docs** at:
- Swagger UI -> [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc -> [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Full Request Pipeline

```
User Prompt
    |
[1]  Lakera Guard — INPUT SCAN        (injection / jailbreak / PII detection)
    | clean
[2]  Security Agent — RBAC CHECK      (role-based access enforcement)
    | authorised
[3]  Retrieval Agent — RAG            (Vector RAG + Graph RAG + web scraping)
    |
[4]  Self-Correcting RAG              (relevance scoring / conflict detection / confidence)
    |
[5]  Lakera Guard — DOCUMENT SCAN     (poisoned chunk detection)
    | clean
[6]  Validation Agent                 (cross-checks results, triggers HITL if needed)
    |
[7]  Tool Agent                       (detects intent, queues plugin actions)
    |
[8]  HITL Gate                        (low confidence or high-risk -> human reviewer)
    | approved
[9]  LLM — OpenAI GPT-4               (structured response generation via ARIA prompt)
    |
[10] Lakera Guard — OUTPUT SCAN       (leakage / PII / hallucination detection)
    | safe
[11] Plugin Execution                 (tools run silently or request confirmation)
    |
[12] LLMOps Logger                    (interaction log: query, agents, tools, security, latency)
    |
Final Response -> User
```

---

## Security Architecture

| Layer              | Component      | What It Does                                            |
|--------------------|----------------|---------------------------------------------------------|
| Input firewall     | Lakera Guard   | Blocks prompt injections, jailbreaks, PII leakage       |
| Access control     | RBAC           | Role-based data category permissions                    |
| Document firewall  | Lakera Guard   | Removes poisoned or malicious RAG chunks                |
| Output firewall    | Lakera Guard   | Prevents data leakage and PII in responses              |
| Audit trail        | LLMOps         | Full PII-stripped interaction log (JSONL)               |
| Escalation gate    | HITL           | Human review for low-confidence / high-risk tasks       |

### RBAC Roles

| Role       | Access Level                                              |
|------------|-----------------------------------------------------------|
| `employee` | General knowledge, public policies, self-service tasks    |
| `manager`  | Team data, reports, scheduling, performance data          |
| `admin`    | Full access including sensitive financial and HR data     |

---

## Agents

| Agent               | Responsibility                                               |
|---------------------|--------------------------------------------------------------|
| `OrchestratorAgent` | Coordinates all agents, assembles the final response         |
| `SecurityAgent`     | Enforces RBAC before any retrieval or action occurs          |
| `RetrievalAgent`    | Runs Vector RAG + Graph RAG + web scraping fallback          |
| `ValidationAgent`   | Cross-checks data, detects conflicts, triggers HITL          |
| `ToolAgent`         | Detects tool intent from queries, queues plugin actions      |

---

## Plugins

All plugins use a shared `BasePlugin` class and support:
- Retry logic with exponential backoff (`@with_retry`)
- Input validation on all required parameters
- Health check (`health_check()`)
- Action discovery (`list_actions()`)
- Structured error codes (`NOT_CONNECTED`, `INVALID_PARAMS`, etc.)

| Plugin            | File                 | Key Actions                                                                       |
|-------------------|----------------------|-----------------------------------------------------------------------------------|
| Google Drive      | `google_drive.py`    | list_files, search_files, upload_file, download_file, delete_file, share_file     |
| Google Docs       | `google_docs.py`     | create_document, get_document, append_content, edit_document, share_document      |
| Google Sheets     | `google_sheets.py`   | create_spreadsheet, read_data, push_data, append_row, clear_range                 |
| Google Calendar   | `google_calendar.py` | list_events, create_event, update_event, delete_event, set_reminder               |
| Gmail             | `gmail.py`           | send_email, draft_email, search_emails, read_email, reply_email, create_label     |
| Google Meet       | `google_meet.py`     | create_meeting, schedule_call (real Meet links via Calendar API)                  |
| Slack             | `slack.py`           | send_message, list_channels, upload_file, reply_to_thread, get_channel_history    |
| Notion            | `notion.py`          | create_page, get_page, search_pages, update_page, append_blocks                   |
| Grafana           | `grafana.py`         | push_metrics, list_dashboards, get_dashboard, create_annotation                   |

### Plugin Registry Usage

```python
from plugins import PluginRegistry

registry = PluginRegistry()

registry.list_plugins()                        # List all available plugins
registry.list_actions("slack")                 # List actions for a specific plugin

result = registry.execute("slack", "send_message", {
    "channel": "#general",
    "message": "Deployment complete"
})

registry.health_report()                       # Health check all plugins
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

| Level    | Trigger                         | SLA              |
|----------|---------------------------------|------------------|
| `LOW`    | Low confidence retrieval        | 30 min (default) |
| `MEDIUM` | Sensitive data category access  | 15 min           |
| `HIGH`   | High-risk irreversible actions  | Immediate        |

---

## Supported Data Ingestion Formats

| Format | Support               |
|--------|-----------------------|
| PDF    | via PyPDF2            |
| DOCX   | via python-docx       |
| XLSX   | via openpyxl          |
| CSV    | native                |
| TXT    | native                |
| JSON   | native                |
| XML    | native                |
| URLs   | via web scraper       |

---

## Contributing

1. **Add a new plugin** -> create `plugins/<name>.py` extending `BasePlugin`
2. **Register it** -> add to `plugins/registry.py` -> `_register_all()`
3. **Wire tool intent** -> add trigger keywords in `agents/multi_agent.py` -> `ToolAgent.TOOL_MAP`
4. **Add credentials** -> update `.env.example` with any new keys needed

---

## Detailed Documentation

For full module-level documentation, see [`enterprise_ai/README.md`](enterprise_ai/README.md).

---

## License

This project is licensed under the **MIT License**.

---

<div align="center">
<sub>Built by <strong>Sagar Rambade</strong> · Nova AI</sub>
</div>
