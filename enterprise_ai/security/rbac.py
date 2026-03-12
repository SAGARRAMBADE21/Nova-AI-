"""
security/rbac.py
Role-Based Access Control
General Data  → all authenticated employees
Confidential  → authorised roles only
"""

from enum import Enum
from typing import Set
import logging

logger = logging.getLogger(__name__)


class Role(Enum):
    EMPLOYEE   = "employee"
    TEAM_LEAD  = "team_lead"
    MANAGER    = "manager"
    ADMIN      = "admin"


class DataCategory(Enum):
    GENERAL      = "general"
    CONFIDENTIAL = "confidential"


# Role → allowed data categories
ROLE_PERMISSIONS: dict[Role, Set[DataCategory]] = {
    Role.EMPLOYEE:  {DataCategory.GENERAL},
    Role.TEAM_LEAD: {DataCategory.GENERAL, DataCategory.CONFIDENTIAL},
    Role.MANAGER:   {DataCategory.GENERAL, DataCategory.CONFIDENTIAL},
    Role.ADMIN:     {DataCategory.GENERAL, DataCategory.CONFIDENTIAL},
}

# Confidential data keywords — trigger access check
CONFIDENTIAL_KEYWORDS = [
    "salary", "payroll", "financial", "revenue", "hr", "personnel",
    "strategic", "confidential", "private", "restricted", "budget",
    "acquisition", "merger", "legal", "compliance",
]


class RBACController:

    def check_access(self, user_role: Role, category: DataCategory) -> bool:
        allowed = ROLE_PERMISSIONS.get(user_role, set())
        granted = category in allowed
        if not granted:
            logger.warning(f"[RBAC] Access denied | role={user_role.value} | category={category.value}")
        return granted

    def classify_query(self, query: str) -> DataCategory:
        """Determine if a query touches confidential data."""
        q = query.lower()
        for keyword in CONFIDENTIAL_KEYWORDS:
            if keyword in q:
                logger.info(f"[RBAC] Confidential keyword detected: '{keyword}'")
                return DataCategory.CONFIDENTIAL
        return DataCategory.GENERAL

    def get_denied_message(self, user_role: Role, category: DataCategory) -> str:
        return (
            f"Access denied. Your role ({user_role.value}) does not have permission "
            f"to access {category.value} data. "
            f"Please contact your manager or system administrator."
        )
