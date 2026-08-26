from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from app.config.enums import GenderChoice


class SongBase(BaseModel):
    title: str
    release_date: date | None = None


class SongCreate(SongBase):
    album_id: int   # required at creation

class SongResponse(SongBase):
    id: int
    album_id: int | None = None   # optional here, a Response for an orphaned song has no album
    created_at: datetime | None = None
    last_update: datetime | None = None
    album: "AlbumBase|None"
    model_config = ConfigDict(from_attributes=True)


class SongUpdate(BaseModel):
    title: str | None = None
    release_date: date | None = None
    album_id: int | None = None


class AlbumBase(BaseModel):
    name: str
    release_date: date | None = None
    author: str | None = None
    group_id: int | None = None


class AlbumCreate(AlbumBase):
    pass


class AlbumResponse(AlbumBase):
    id: int
    songs: list[SongBase] = []
    group: "GroupBase|None"
    slug: str
    model_config = ConfigDict(from_attributes=True)


class AlbumUpdate(BaseModel):
    name: str | None = None
    release_date: date | None = None
    author: str | None = None
    group_id: int | None = None


class GroupBase(BaseModel):
    name: str


class GroupCreate(GroupBase):
    pass


class GroupResponse(GroupBase):
    id: int
    albums: list[AlbumBase] | None = []
    members: list["IdolBase"] | None = []
    slug: str
    model_config = ConfigDict(from_attributes=True)


class GroupUpdate(BaseModel):
    name: str | None = None


class IdolBase(BaseModel):
    stage_name: str
    full_name: str | None = None
    korean_name: str | None = None
    korean_stage_name: str | None = None
    birth_date: date | None = None
    gender: GenderChoice | None
    birth_place: str | None = None
    country: str | None = None
    instagram_username: str | None = None


# gotta add date validation here


class IdolCreate(IdolBase):
    group_id: int | None = None


class IdolResponse(IdolBase):
    id: int
    group: GroupBase | None = None
    slug: str | None = None
    model_config = ConfigDict(from_attributes=True)


class IdolUpdate(BaseModel):
    stage_name: str | None = None
    full_name: str | None = None
    korean_name: str | None = None
    korean_stage_name: str | None = None
    birth_date: date | None = None
    gender: GenderChoice | None
    birth_place: str | None = None
    country: str | None = None
    instagram_username: str | None = None
    group_id: int | None = None
