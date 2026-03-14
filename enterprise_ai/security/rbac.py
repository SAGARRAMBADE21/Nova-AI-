"""
security/rbac.py
Role-Based Access Control — Dual Vector Database approach
  DB 1 (public_knowledge)  → accessible by ALL roles
  DB 2 (private_knowledge) → accessible by TEAM_LEAD, MANAGER, ADMIN only
"""

from enum import Enum
from typing import List
import logging

logger = logging.getLogger(__name__)


class Role(Enum):
    EMPLOYEE  = "employee"
    TEAM_LEAD = "team_lead"
    MANAGER   = "manager"
    ADMIN     = "admin"


# Which ChromaDB collections each role can query
ROLE_DB_ACCESS: dict[Role, List[str]] = {
    Role.EMPLOYEE:  ["public_knowledge"],
    Role.TEAM_LEAD: ["public_knowledge", "private_knowledge"],
    Role.MANAGER:   ["public_knowledge", "private_knowledge"],
    Role.ADMIN:     ["public_knowledge", "private_knowledge"],
}


class RBACController:

    def get_allowed_collections(self, user_role: Role) -> List[str]:
        """Return the list of ChromaDB collections the role can query."""
        collections = ROLE_DB_ACCESS.get(user_role, ["public_knowledge"])
        logger.info(f"[RBAC] role={user_role.value} | collections={collections}")
        return collections

    def can_access_private(self, user_role: Role) -> bool:
        """Quick check — can this role see private/company data?"""
        return "private_knowledge" in ROLE_DB_ACCESS.get(user_role, [])

    def get_denied_message(self, user_role: Role) -> str:
        return (
            f"Access denied. Your role ({user_role.value}) can only access the public "
            f"knowledge base. Please contact your manager or administrator for access "
            f"to internal company data."
        )
