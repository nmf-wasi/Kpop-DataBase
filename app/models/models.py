from app.database.database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, DateTime, Date, ForeignKey, Index, Enum as SQLEnum
from app.config.enums import UserRole, GenderChoice
from datetime import datetime
from datetime import date


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


class Song(Base):
    """Song table, has Mto1 relationship with ALbum"""

    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    release_date: Mapped[date|None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_update: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    album_id: Mapped[int | None] = mapped_column(  # now nullable
        Integer, ForeignKey("albums.id", ondelete="SET NULL"), nullable=True
    )  # the FK always lives on the "many" side

    album: Mapped["Album|None"] = relationship(back_populates="songs")
    # back populates song col on Album table

    __table_args__ = (
        Index("idx_song_title", "title"),
        Index("idx_song_album_id", "album_id"),
    )


class Album(Base):
    """Album table, has 1toM relation with Songs and Mto1 with Group"""

    __tablename__ = "albums"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    release_date: Mapped[date|None] = mapped_column(Date, nullable=True)
    author: Mapped[str | None] = mapped_column(String, nullable=True)
    songs: Mapped[list["Song"]] = relationship(
        back_populates="album",  # write the table_name, not the className
        passive_deletes=True,  # let the db handle the SET NULL,
    )
    group_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "groups.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    group: Mapped["Group"] = relationship(
        back_populates="albums",
    )
    slug: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
    )

    __table_args__ = (Index("idx_album_group_id", "group_id"),)


class Group(Base):
    """Group Table, has 1toM relation with both Albums and Idols"""

    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    albums: Mapped[list["Album"]] = relationship(
        back_populates="group",
        passive_deletes=True,  # Trust db to set null, no need for manual handling
    )
    members: Mapped[list["Idol"]] = relationship(
        back_populates="group",
        passive_deletes=True,
    )
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)


class Idol(Base):
    """has 1toM wth Groups, so hold the fk, back_populates group's members col"""

    __tablename__ = "idols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stage_name: Mapped[str] = mapped_column()
    full_name: Mapped[str | None] = mapped_column(nullable=True)
    korean_name: Mapped[str | None] = mapped_column(nullable=True)
    korean_stage_name: Mapped[str | None] = mapped_column(nullable=True)
    birth_date: Mapped[date | None] = mapped_column(nullable=True)
    birth_place: Mapped[str | None] = mapped_column(nullable=True)
    group_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "groups.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    group: Mapped["Group|None"] = relationship(back_populates="members")
    country: Mapped[str | None] = mapped_column(nullable=True)
    instagram_username: Mapped[str | None] = mapped_column(nullable=True)
    gender: Mapped[GenderChoice|None] = mapped_column(SQLEnum(GenderChoice),nullable=True)
    slug = mapped_column(String, unique=True, index=True)

    __table_args__ = (
        Index("idx_idol_country", "country"),
        Index("idx_idol_group_id", "group_id"),
        Index("idx_idol_stage_name", "stage_name"),
    )
