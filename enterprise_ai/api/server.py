"""
api/server.py
FastAPI REST Server — exposes the assistant via HTTP endpoints
POST /chat          — user query or task
POST /ingest        — admin document upload
GET  /metrics       — LLMOps dashboard metrics
GET  /health        — health check
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import uvicorn
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import EnterpriseAIAssistant
from security.rbac import Role

app       = FastAPI(title="Enterprise AI Assistant", version="1.0.0")
assistant = EnterpriseAIAssistant()


# ── Request / Response models ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    prompt:     str
    user_id:    str
    user_role:  str = "employee"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response:   str
    session_id: Optional[str]


class IngestRequest(BaseModel):
    file_path:   str
    category:    str = "general"
    uploaded_by: str = "admin"


# ── Endpoints ─────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        role = Role(request.user_role)
    except ValueError:
        role = Role.EMPLOYEE

    response = assistant.chat(
        user_prompt = request.prompt,
        user_id     = request.user_id,
        user_role   = role,
        session_id  = request.session_id,
    )
    return ChatResponse(response=response, session_id=request.session_id)


@app.post("/ingest")
async def ingest(request: IngestRequest):
    result = assistant.ingest_document(
        file_path   = request.file_path,
        category    = request.category,
        uploaded_by = request.uploaded_by,
    )
    if result.get("status") == "failed":
        raise HTTPException(status_code=400, detail=result.get("reason"))
    return result


@app.get("/metrics")
async def metrics():
    return assistant.get_metrics()


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
