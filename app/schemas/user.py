from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from app.config.enums import UserRole
from datetime import datetime


class UserBase(BaseModel):
    """Base Scheema of the User class"""

    first_name: str | None = None
    last_name: str | None = None
    username: str
    email: EmailStr


class UserResponse(UserBase):
    """Returns the user details"""

    id: int
    role: UserRole
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime | None
    updated_profile_at: datetime
    last_login: datetime | None = None


class UserCreate(UserBase):
    """User create schema, also verifies the length of username"""

    password: str

    @field_validator("username")
    @classmethod
    def username_min_length(cls, username: str) -> str:
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters!")
        return username


class UserUpdate(BaseModel):
    """User update schema, everything is optional here to provide maximum flexibility to update, but we won't let users change password here, that has a separate endpoint"""

    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    email: EmailStr | None = None


class LoginResponse(BaseModel):
    """When user logs in, return access and refresh token"""

    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    """Take the refresh token as input when user tries to get a new access and refresh token"""

    refresh_token: str
