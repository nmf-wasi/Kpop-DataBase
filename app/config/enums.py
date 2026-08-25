from enum import Enum


class UserRole(str, Enum):
    """Add user roles here, when new roles are added, do alembic migrations"""
    USER = "user"
    ADMIN = "admin"

class GenderChoice(str, Enum):
    """Gives Gender choice to idols"""
    MALE="male"
    FEMALE="female"