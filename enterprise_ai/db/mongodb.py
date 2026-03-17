"""
db/mongodb.py
MongoDB Atlas client — replaces ChromaDB entirely.

TenantManager    — companies, users, audit_logs collections (metadata)
TenantVectorStore — knowledge_vectors collection with Atlas Vector Search
"""

import os
import logging
import hashlib
import secrets as _secrets
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


# ── Connection ────────────────────────────────────────────────────────────

def get_mongodb_client():
    """Connect to MongoDB Atlas and return (client, db)."""
    from pymongo import MongoClient
    uri     = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "nova_ai")
    client  = MongoClient(uri)
    db      = client[db_name]
    logger.info(f"[MongoDB] Connected | db={db_name}")
    return client, db


# ── Tenant Manager ────────────────────────────────────────────────────────

class TenantManager:
    """
    Manages company/tenant onboarding and user records.

    Collections:
        companies   — one doc per company workspace
        users       — one doc per user per tenant
        audit_logs  — interaction audit trail per tenant
    """

    def __init__(self, db):
        self.db         = db
        self.companies  = db["companies"]
        self.users      = db["users"]
        self.audit_logs = db["audit_logs"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        try:
            self.companies.create_index("tenant_id",  unique=True)
            self.companies.create_index("join_code",  unique=True)
            self.users.create_index(
                [("tenant_id", 1), ("email", 1)], unique=True
            )
        except Exception as e:
            logger.warning(f"[TenantManager] Index warning: {e}")

    # ── Company ───────────────────────────────────────────────────────────

    def create_company(self, company_name: str,
                       admin_email: str, tenant_id: str) -> dict:
        """Create a new company workspace and return its join code."""
        import secrets
        join_code = secrets.token_urlsafe(8).upper()[:12]

        company = {
            "tenant_id":    tenant_id,
            "company_name": company_name,
            "admin_email":  admin_email,
            "join_code":    join_code,
            "created_at":   datetime.utcnow().isoformat(),
            "status":       "active",
        }
        self.companies.update_one(
            {"tenant_id": tenant_id},
            {"$set": company},
            upsert=True,
        )
        logger.info(
            f"[TenantManager] Company created | "
            f"tenant={tenant_id} | name={company_name}"
        )
        return {"tenant_id": tenant_id,
                "join_code": join_code,
                "company_name": company_name}

    def get_company_by_code(self, join_code: str) -> Optional[dict]:
        return self.companies.find_one(
            {"join_code": join_code.upper()}, {"_id": 0}
        )

    def get_company_by_tenant_id(self, tenant_id: str) -> Optional[dict]:
        return self.companies.find_one({"tenant_id": tenant_id}, {"_id": 0})

    # ── Email Config (admin's sender Gmail) ───────────────────────────────

    def _fernet(self):
        """Build a Fernet cipher from NOVA_JWT_SECRET."""
        import base64
        from cryptography.fernet import Fernet
        secret = os.getenv("NOVA_JWT_SECRET", "default-secret-change-me")
        # Fernet key must be 32 url-safe base64 bytes
        key = base64.urlsafe_b64encode(
            hashlib.sha256(secret.encode()).digest()
        )
        return Fernet(key)

    def set_email_config(self, tenant_id: str,
                         sender_email: str, app_password: str) -> bool:
        """
        Store admin's Gmail credentials (app_password encrypted).
        Called from POST /email-config on the admin dashboard.
        """
        encrypted = self._fernet().encrypt(app_password.encode()).decode()
        self.companies.update_one(
            {"tenant_id": tenant_id},
            {"$set": {
                "sender_email":    sender_email,
                "sender_password": encrypted,   # encrypted, never stored plain
            }},
        )
        logger.info(
            f"[TenantManager] Email config saved | tenant={tenant_id}"
        )
        return True

    def get_email_config(self, tenant_id: str) -> Optional[dict]:
        """
        Return decrypted sender email and app_password for this tenant.
        Returns None if not configured.
        """
        company = self.get_company_by_tenant_id(tenant_id)
        if not company or "sender_email" not in company:
            return None
        try:
            decrypted = self._fernet().decrypt(
                company["sender_password"].encode()
            ).decode()
            return {
                "sender_email":    company["sender_email"],
                "sender_password": decrypted,
            }
        except Exception as e:
            logger.error(f"[TenantManager] Email config decrypt error: {e}")
            return None

    # ── Password (for non-admin users) ──────────────────────────────────────

    @staticmethod
    def _hash_password(password: str) -> str:
        """PBKDF2-SHA256 password hash (no external deps)."""
        salt = _secrets.token_hex(16)
        key  = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 200_000
        )
        return f"{salt}${key.hex()}"

    @staticmethod
    def _verify_hash(password: str, hashed: str) -> bool:
        """Constant-time comparison of PBKDF2 hash."""
        try:
            salt, stored_key = hashed.split("$", 1)
            new_key = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), salt.encode(), 200_000
            )
            return _secrets.compare_digest(new_key.hex(), stored_key)
        except Exception:
            return False

    def set_password(self, tenant_id: str, email: str, password: str) -> bool:
        """Hash and store a password for a user. Returns True if user exists."""
        hashed = self._hash_password(password)
        result = self.users.update_one(
            {"tenant_id": tenant_id, "email": email},
            {"$set": {"password_hash": hashed, "status": "active"}},
        )
        return result.matched_count > 0

    def verify_user_password(self, tenant_id: str,
                             email: str, password: str) -> bool:
        """Return True if email+password match for this tenant."""
        user = self.get_user(tenant_id, email)
        if not user or "password_hash" not in user:
            return False
        return self._verify_hash(password, user["password_hash"])

    # ── Users ─────────────────────────────────────────────────────────────

    def add_user(self, tenant_id: str, email: str, role: str,
                 clerk_user_id: str = "", invited_by: str = "") -> dict:
        """
        Add or update a user in a tenant workspace.
        role: 'employee' | 'manager' | 'team_lead' | 'admin'
        """
        user = {
            "tenant_id":     tenant_id,
            "email":         email,
            "role":          role,
            "clerk_user_id": clerk_user_id,
            "invited_by":    invited_by,
            "status":        "invited",
            "created_at":    datetime.utcnow().isoformat(),
        }
        self.users.update_one(
            {"tenant_id": tenant_id, "email": email},
            {"$set": user},
            upsert=True,
        )
        logger.info(
            f"[TenantManager] User upserted | tenant={tenant_id} "
            f"| email={email} | role={role}"
        )
        return user

    def get_user(self, tenant_id: str, email: str) -> Optional[dict]:
        return self.users.find_one(
            {"tenant_id": tenant_id, "email": email}, {"_id": 0}
        )

    def list_users(self, tenant_id: str) -> List[dict]:
        return list(
            self.users.find(
                {"tenant_id": tenant_id},
                {"_id": 0, "password_hash": 0},
            )
        )

    def update_user_status(self, tenant_id: str, email: str,
                           status: str) -> bool:
        result = self.users.update_one(
            {"tenant_id": tenant_id, "email": email},
            {"$set": {"status": status}},
        )
        return result.modified_count > 0

    # ── Audit ─────────────────────────────────────────────────────────────

    def log_audit(self, tenant_id: str, log_entry: dict):
        """Append a PII-stripped audit log entry for this tenant."""
        self.audit_logs.insert_one({**log_entry, "tenant_id": tenant_id})


# ── Tenant Vector Store ───────────────────────────────────────────────────

class TenantVectorStore:
    """
    MongoDB Atlas Vector Search — replaces ChromaDB.

    Collection: 'knowledge_vectors'
    Document schema:
        _id         — MD5 hash of (tenant_id + source + timestamp + content[:50])
        tenant_id   — company/workspace scope (RBAC isolation)
        db_type     — 'public' | 'private'  (RBAC access filter)
        content     — original text chunk
        source      — filename or URL
        embedding   — float[1536] (text-embedding-3-small)
        category    — e.g. 'hr', 'finance', 'general'
        ingested_at — ISO timestamp

    ⚠️  Atlas Setup Required:
        Create a Vector Search index named 'vector_index' in Atlas UI on
        collection 'knowledge_vectors' with:
            field      : embedding
            dimensions : 1536
            similarity : cosine
    """

    COLLECTION_NAME = "knowledge_vectors"
    EMBEDDING_DIM   = 1536   # text-embedding-3-small

    def __init__(self, db, openai_client):
        self.col    = db[self.COLLECTION_NAME]
        self.openai = openai_client
        self._ensure_regular_indexes()
        logger.info("[TenantVectorStore] MongoDB Atlas Vector Store ready.")
        logger.info(
            "[TenantVectorStore] ⚠️  Ensure Atlas Vector Search index "
            "'vector_index' is created on 'knowledge_vectors' → "
            f"field='embedding', dimensions={self.EMBEDDING_DIM}, similarity=cosine."
        )

    def _ensure_regular_indexes(self):
        """Create regular (non-vector) indexes for query filter efficiency."""
        try:
            self.col.create_index([("tenant_id", 1), ("db_type", 1)])
            self.col.create_index("source")
        except Exception as e:
            logger.warning(f"[TenantVectorStore] Index warning: {e}")

    # ── Embedding ─────────────────────────────────────────────────────────

    def _embed(self, text: str) -> List[float]:
        """Generate embedding via OpenAI Embeddings API."""
        model    = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        response = self.openai.embeddings.create(
            input=[text[:8000]],   # Truncate to model token limit
            model=model,
        )
        return response.data[0].embedding

    # ── Write ─────────────────────────────────────────────────────────────

    def add_document(self, tenant_id: str, content: str,
                     source: str, timestamp: str,
                     category: str = "general",
                     db_type: str  = "public") -> str:
        """
        Embed content and store in Atlas.

        db_type='public'  → all roles (employee, manager, team_lead, admin)
        db_type='private' → restricted (manager, team_lead, admin only)
        """
        doc_id = hashlib.md5(
            f"{tenant_id}{source}{timestamp}{content[:50]}".encode()
        ).hexdigest()

        try:
            embedding = self._embed(content)
        except Exception as e:
            logger.error(f"[TenantVectorStore] Embedding error: {e}")
            embedding = [0.0] * self.EMBEDDING_DIM  # zero-vector fallback

        document = {
            "_id":         doc_id,
            "tenant_id":   tenant_id,
            "db_type":     db_type,
            "content":     content,
            "source":      source,
            "timestamp":   timestamp,
            "category":    category,
            "embedding":   embedding,
            "ingested_at": datetime.utcnow().isoformat(),
        }
        self.col.replace_one({"_id": doc_id}, document, upsert=True)
        logger.info(
            f"[TenantVectorStore] Stored | tenant={tenant_id} "
            f"| db_type={db_type} | source={source}"
        )
        return doc_id

    # ── Read ──────────────────────────────────────────────────────────────

    def search(self, tenant_id: str, query: str,
               allowed_db_types: List[str],
               top_k: int = 5) -> List[dict]:
        """
        Semantic search filtered by tenant_id and RBAC-resolved db_types.
        Uses MongoDB Atlas $vectorSearch aggregation stage.
        """
        try:
            query_embedding = self._embed(query)
        except Exception as e:
            logger.error(f"[TenantVectorStore] Query embedding error: {e}")
            return []

        pipeline = [
            {
                "$vectorSearch": {
                    "index":         "vector_index",
                    "path":          "embedding",
                    "queryVector":   query_embedding,
                    "numCandidates": top_k * 10,
                    "limit":         top_k,
                    "filter": {
                        "tenant_id": {"$eq": tenant_id},
                        "db_type":   {"$in": allowed_db_types},
                    },
                }
            },
            {
                "$project": {
                    "content":   1,
                    "source":    1,
                    "timestamp": 1,
                    "category":  1,
                    "db_type":   1,
                    "score":     {"$meta": "vectorSearchScore"},
                    "_id":       0,
                }
            },
        ]

        try:
            results = list(self.col.aggregate(pipeline))
            logger.info(
                f"[TenantVectorStore] Search | tenant={tenant_id} "
                f"| db_types={allowed_db_types} | hits={len(results)}"
            )
            return results
        except Exception as e:
            logger.error(f"[TenantVectorStore] Vector search error: {e}")
            return []

    # ── Delete ────────────────────────────────────────────────────────────

    def list_documents(self, tenant_id: str) -> List[dict]:
        """Return one summary row per ingested source file for this tenant."""
        pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id":        "$source",
                "db_type":    {"$first": "$db_type"},
                "category":   {"$first": "$category"},
                "ingested_at": {"$max": "$ingested_at"},
            }},
            {"$project": {
                "source":     "$_id",
                "db_type":    1,
                "category":   1,
                "ingested_at": 1,
                "_id":        0,
            }},
            {"$sort": {"ingested_at": -1}},
        ]
        try:
            return list(self.col.aggregate(pipeline))
        except Exception as e:
            logger.error(f"[TenantVectorStore] list_documents error: {e}")
            return []

    def delete_tenant_data(self, tenant_id: str) -> int:
        """Remove all vector data for a tenant (GDPR / offboarding)."""
        result = self.col.delete_many({"tenant_id": tenant_id})
        logger.info(
            f"[TenantVectorStore] Purged {result.deleted_count} docs "
            f"| tenant={tenant_id}"
        )
        return result.deleted_count
