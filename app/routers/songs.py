from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, asc, desc
from app.database.database import get_db
from app.models import models
from app.schemas.kpop import SongCreate, SongResponse, SongUpdate, PaginationResponse
from app.config.enums import SongSortFields, SortOrder, UserRole
from app.dependencies import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=PaginationResponse[SongResponse])
def get_songs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: SongSortFields = SongSortFields.TITLE,
    order_by: SortOrder = SortOrder.ASC,
    album_id: int | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):

    # get sort and order by vals
    sort_col = getattr(models.Song, sort_by.value)
    order_func = desc if order_by == SortOrder.DESC else asc

    # base queryset
    queryset = select(models.Song).options(
        selectinload(models.Song.album),
    )
    count_queryset = select(func.count()).select_from(models.Song)


    filters = []
    # search
    if search is not None:
        filters.append(models.Song.title.ilike(f"%{search}%"))
    # filters
    if album_id is not None:
        filters.append(models.Song.album_id == album_id)

    queryset = queryset.where(*filters)
    count_queryset = count_queryset.where(*filters)

    # sort
    queryset = queryset.order_by(order_func(sort_col))

    # pagination
    queryset = queryset.offset(skip).limit(limit)
    return {
        "total": db.execute(count_queryset).scalar_one(),
        "skip": skip,
        "limit": limit,
        "items": db.execute(queryset).scalars().all(),
    }


@router.get("/{song_id}", response_model=SongResponse)
def get_song(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    song = db.execute(
        select(models.Song)
        .options(
            selectinload(models.Song.album),
        )
        .where(models.Song.id == song_id)
    ).scalar_one_or_none()
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song not found!",
        )
    return song


@router.post("/", response_model=SongResponse)
def create_song(
    song_data: SongCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(UserRole.ADMIN)),
):
    """ """
    album = db.execute(
        select(models.Album).where(
            models.Album.id == song_data.album_id,
        )
    ).scalar_one_or_none()
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album doesn't exists!",
        )

    song_exists = db.execute(
        select(models.Song).where(
            models.Song.title == song_data.title,
            models.Song.album_id == song_data.album_id,
        )
    ).scalar_one_or_none()
    if song_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another song with same name already exists in this album",
        )

    new_song = models.Song()
    for key, value in song_data.model_dump().items():
        setattr(new_song, key, value)
    db.add(new_song)
    db.commit()
    db.refresh(new_song)
    return new_song


@router.patch("/{song_id}", response_model=SongResponse)
def update_song(
    song_id: int,
    song_data: SongUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(UserRole.ADMIN)),
):
    song = db.execute(
        select(models.Song).where(models.Song.id == song_id)
    ).scalar_one_or_none()
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song does not exists!"
        )
    if song_data.album_id:
        album = db.execute(
            select(models.Album).where(
                models.Album.id == song_data.album_id,
            )
        ).scalar_one_or_none()
        if not album:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Album doesn't exists!",
            )

    if song_data.title and song_data.album_id:
        song_exists = db.execute(
            select(models.Song).where(
                models.Song.title == song_data.title,
                models.Song.album_id == song_data.album_id,
                models.Song.id != song_id,
            )
        ).scalar_one_or_none()
        if song_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another song with same name already exists in this album",
            )
    updated_data = song_data.model_dump(exclude_unset=True)

    for key, value in updated_data.items():
        setattr(song, key, value)
    db.commit()
    db.refresh(song)
    return song


@router.delete("/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_song(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(UserRole.ADMIN)),
):
    song = db.execute(
        select(models.Song).where(models.Song.id == song_id)
    ).scalar_one_or_none()
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song does not exists!"
        )
    db.delete(song)
    db.commit()
