from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, asc, desc
from app.database.database import get_db
from app.models import models
from app.schemas.kpop import AlbumCreate, AlbumResponse, AlbumUpdate, PaginationResponse
from app.utils.slug import slugify
from app.config.enums import SortOrder, AlbumSortFields

router = APIRouter()


@router.get("/", response_model=PaginationResponse[AlbumResponse])
def get_albums(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: AlbumSortFields = AlbumSortFields.NAME,
    order_by: SortOrder = SortOrder.ASC,
    author: str | None = None,
    group_id: int | None = None,
    db: Session = Depends(get_db),
):

    # get sort and order by vals
    sort_col = getattr(models.Album, sort_by.value)
    order_func = desc if order_by == SortOrder.DESC else asc

    # base query
    queryset = select(models.Album).options(
        selectinload(models.Album.songs),
        selectinload(models.Album.group),
    )
    count_queryset = select(func.count()).select_from(models.Album)

    # filters
    filters = []
    if author is not None:
        filters.append(models.Album.author == author)
    if group_id is not None:
        filters.append(models.Album.group_id == group_id)

    queryset = queryset.where(*filters)
    count_queryset = count_queryset.where(*filters)

    # sort
    queryset = queryset.order_by(order_func(sort_col))

    # Pagination
    queryset = queryset.offset(skip).limit(limit)
    return {
        "total": db.execute(count_queryset).scalar_one(),
        "skip": skip,
        "limit": limit,
        "items": db.execute(queryset).scalars().all(),
    }


@router.get("/{album_id}", response_model=AlbumResponse)
def get_album(album_id: int, db: Session = Depends(get_db)):
    album = db.execute(
        select(models.Album)
        .options(
            selectinload(models.Album.songs),
            selectinload(models.Album.group),
        )
        .where(models.Album.id == album_id)
    ).scalar_one_or_none()
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found!",
        )
    return album


@router.post("/", response_model=AlbumResponse)
def create_album(album_data: AlbumCreate, db: Session = Depends(get_db)):
    album_exists = db.execute(
        select(models.Album).where(
            models.Album.name == album_data.name,
            models.Album.group_id == album_data.group_id,
        )
    ).scalar_one_or_none()
    if album_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Album with same name exists for this group",
        )

    if album_data.group_id:
        group_exists = db.execute(
            select(models.Group).where(
                models.Group.id == album_data.group_id,
            )
        ).scalar_one_or_none()
        if not group_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found!",
            )

    new_album = models.Album()
    for key, value in album_data.model_dump().items():
        setattr(new_album, key, value)
    slugs = db.execute(select(models.Album.slug)).scalars().all()
    new_slug = slugify(album_data.name, slugs)
    new_album.slug = new_slug
    db.add(new_album)
    db.commit()
    db.refresh(new_album)
    return new_album


@router.patch("/{album_id}", response_model=AlbumResponse)
def update_album(album_id: int, album_data: AlbumUpdate, db: Session = Depends(get_db)):
    album = db.execute(
        select(models.Album).where(
            models.Album.id == album_id,
        )
    ).scalar_one_or_none()
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found!",
        )
    if album_data.group_id:
        group_exists = db.execute(
            select(models.Group).where(
                models.Group.id == album_data.group_id,
            )
        ).scalar_one_or_none()
        if not group_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found!",
            )

    if album_data.name and album_data.group_id:
        album_exists = db.execute(
            select(models.Album).where(
                models.Album.name == album_data.name,
                models.Album.group_id == album_data.group_id,
                models.Album.id != album_id,
            )
        ).scalar_one_or_none()
        if album_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Album with same name exists for this group",
            )

    updated_data = album_data.model_dump(exclude_unset=True)
    for key, value in updated_data.items():
        setattr(album, key, value)
    if album_data.name:
        slugs = (
            db.execute(select(models.Album.slug).where(models.Album.id != album_id))
            .scalars()
            .all()
        )
        new_slug = slugify(album_data.name, slugs)
        album.slug = new_slug

    db.commit()
    db.refresh(album)
    return album


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(album_id: int, db: Session = Depends(get_db)):
    album = db.execute(
        select(models.Album).where(
            models.Album.id == album_id,
        )
    ).scalar_one_or_none()
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found!",
        )
    db.delete(album)
    db.commit()
