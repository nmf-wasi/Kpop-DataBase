from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, asc, desc
from app.database.database import get_db
from app.models import models
from app.schemas.kpop import SongCreate, SongResponse, SongUpdate, PaginationResponse
from app.config.enums import SongSortFields, SortOrder

router = APIRouter()


@router.get("/", response_model=PaginationResponse[SongResponse])
def get_songs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: SongSortFields = SongSortFields.TITLE,
    order_by: SortOrder = SortOrder.ASC,
    db: Session = Depends(get_db),
):

    # get sort and order by vals
    sort_col = getattr(models.Song, sort_by.value)
    order_func = desc if order_by == SortOrder.DESC else asc

    # base queryset
    queryset = select(models.Song)

    # sort
    queryset = queryset.order_by(order_func(sort_col))

    # pagination
    queryset = queryset.offset(skip).limit(limit)
    return {
        "total": db.execute(select(func.count()).select_from(models.Song)).scalar_one(),
        "skip": skip,
        "limit": limit,
        "items": db.execute(queryset).scalars().all(),
    }


@router.get("/{song_id}", response_model=SongResponse)
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = db.execute(
        select(models.Song).where(models.Song.id == song_id)
    ).scalar_one_or_none()
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song not found!",
        )
    return song


@router.post("/", response_model=SongResponse)
def create_song(song_data: SongCreate, db: Session = Depends(get_db)):
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
def update_song(song_id: int, song_data: SongUpdate, db: Session = Depends(get_db)):
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
def delete_song(song_id: int, db: Session = Depends(get_db)):
    song = db.execute(
        select(models.Song).where(models.Song.id == song_id)
    ).scalar_one_or_none()
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song does not exists!"
        )
    db.delete(song)
    db.commit()
