from enum import Enum


class UserRole(str, Enum):
    """Add user roles here, when new roles are added, do alembic migrations"""
    USER = "user"
    ADMIN = "admin"
