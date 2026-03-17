"""
security/rbac.py
Role-Based Access Control — Dual DB approach (MongoDB Atlas)

  db_type='public'  → accessible by ALL roles
  db_type='private' → accessible by TEAM_LEAD, MANAGER, ADMIN only
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


# Which db_types each role can query in MongoDB Atlas
ROLE_DB_ACCESS: dict[Role, List[str]] = {
    Role.EMPLOYEE:  ["public"],
    Role.TEAM_LEAD: ["public", "private"],
    Role.MANAGER:   ["public", "private"],
    Role.ADMIN:     ["public", "private"],
}


class RBACController:

    def get_allowed_db_types(self, user_role: Role) -> List[str]:
        """
        Return the list of db_type values the role can query.
        Returns ['public'] or ['public', 'private'].
        Used by TenantVectorStore.search() as the Atlas filter.
        """
        db_types = ROLE_DB_ACCESS.get(user_role, ["public"])
        logger.info(f"[RBAC] role={user_role.value} | db_types={db_types}")
        return db_types

    def can_access_private(self, user_role: Role) -> bool:
        """Quick check — can this role see private/confidential data?"""
        return "private" in ROLE_DB_ACCESS.get(user_role, [])

    def get_denied_message(self, user_role: Role) -> str:
        return (
            f"Access denied. Your role ({user_role.value}) can only access "
            f"the public knowledge base. Please contact your manager or "
            f"administrator for access to confidential company data."
        )
