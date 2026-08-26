from enum import Enum


class UserRole(str, Enum):
    """Add user roles here, when new roles are added, do alembic migrations"""

    USER = "user"
    ADMIN = "admin"


class GenderChoice(str, Enum):
    """Gives Gender choice to idols"""

    MALE = "M"
    FEMALE = "F"
    # the name we use = the value stored in db


class SortOrder(str, Enum):
    """Sort by ascending or desending order"""

    ASC = "asc"
    DESC = "desc"


class IdolSortFields(str, Enum):
    """Allows users only to sort by certain fields"""

    ID = "id"
    STAGE_NAME = "stage_name"
    BIRTH_DATE = "birth_date"
    BIRTH_PLACE = "birth_place"
    GROUP = "group_id"
    COUNTRY = "country"
    GENDER = "gender"


class GroupSortFields(str, Enum):
    """Allows users to only sort groups by allowed fields"""

    ID = "id"
    NAME = "name"


class AlbumSortFields(str, Enum):
    """Allows users to only sort albums by allowed fields"""

    ID = "id"
    NAME = "name"
    RELEASE_DATE = "release_date"
    AUTHOR = "author"
    GROUP = "group_id"


class SongSortFields(str, Enum):
    """Allows users to only sort songs by allowed fields"""
    ID = 'id'
    TITLE = 'title'
    RELEASE_DATE = 'release_date'
    LAST_UPDATE = 'last_update'
    ALBUM_ID = 'album_id'