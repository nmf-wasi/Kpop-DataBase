from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.database import get_db
from app.models import models
from app.schemas.kpop import GroupCreate, GroupResponse, GroupUpdate
from app.utils.slug import slugify

router = APIRouter()


@router.get("/", response_model=list[GroupResponse])
def get_groups(db: Session = Depends(get_db)):
    return db.execute(select(models.Group)).scalars().all()


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: int, db: Session = Depends(get_db)):
    group = db.execute(
        select(models.Group).where(models.Group.id == group_id)
    ).scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found!",
        )
    return group


@router.post("/", response_model=GroupResponse)
def create_group(group_data: GroupCreate, db: Session = Depends(get_db)):
    group_exists = db.execute(
        select(models.Group).where(models.Group.name == group_data.name)
    ).scalar_one_or_none()
    if group_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Group with same name already exists!",
        )
    new_group = models.Group()
    for key, value in group_data.model_dump().items():
        setattr(new_group, key, value)

    slugs = db.execute(select(models.Group.slug)).scalars().all()
    new_slug = slugify(new_group.name, slugs)
    new_group.slug = new_slug
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(group_id: int, group_data: GroupUpdate, db: Session = Depends(get_db)):
    group = db.execute(
        select(models.Group).where(models.Group.id == group_id)
    ).scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found!",
        )

    if group_data.name:
        name_exists = db.execute(
            select(models.Group).where(
                models.Group.name == group_data.name,
                models.Group.id != group_id,
            )
        ).scalar_one_or_none()
        if name_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Group name already exists!",
            )
    updated_data = group_data.model_dump(exclude_unset=True)
    for key, value in updated_data.items():
        setattr(group, key, value)
    if group_data.name:
        slugs = (
            db.execute(select(models.Group.slug).where(models.Group.id != group_id))
            .scalars()
            .all()
        )
        new_slug = slugify(group_data.name, slugs)
        group.slug = new_slug

    db.commit()
    db.refresh(group)
    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, db: Session = Depends(get_db)):
    group = db.execute(
        select(models.Group).where(models.Group.id == group_id)
    ).scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found!",
        )
    db.delete(group)
    db.commit()
