from app.database.database import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Integer, String, DateTime
from app.config.enums import UserRole
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)

    username: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str | None] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)

    role: Mapped[UserRole] = mapped_column(default=UserRole.USER)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    # dont call datetime.now() or else it will be executed everytime we touch a row
    updated_profile_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None
    )
