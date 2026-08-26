from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.database import get_db
from app.models import models
from app.schemas.kpop import IdolCreate, IdolResponse, IdolUpdate
from app.utils.slug import slugify

router = APIRouter()


@router.get("/", response_model=list[IdolResponse])
def get_idols(db: Session = Depends(get_db)):
    # pagination is a must here, or response takes too long
    return db.execute(select(models.Idol)).scalars().all()


@router.get("/{idol_id}", response_model=IdolResponse)
def get_idol(
    idol_id: int,
    db: Session = Depends(get_db),
):
    idol = db.execute(
        select(models.Idol).where(models.Idol.id == idol_id)
    ).scalar_one_or_none()
    if not idol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idol not found!",
        )
    return idol


@router.post("/", response_model=IdolResponse)
def create_idol(
    idol_data: IdolCreate,
    db: Session = Depends(get_db),
):
    if idol_data.group_id:
        group = db.execute(
            select(models.Group).where(models.Group.id == idol_data.group_id)
        ).scalar_one_or_none()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group doesn't exists!",
            )
    # can we somehow check if the username exists on ig? like send a req and get a 200 response, then it means there is?

    # check if the same name idol exists, group name and stage name would do
    idol_exists = db.execute(
        select(models.Idol).where(
            models.Idol.stage_name == idol_data.stage_name,
            models.Idol.group_id == idol_data.group_id,
        )
    ).scalar_one_or_none()
    if idol_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idol from same group with same stage name already exists!",
        )
    new_idol = models.Idol()
    for key, value in idol_data.model_dump().items():
        setattr(new_idol, key, value)

    if idol_data.group_id:
        new_idol.group = db.execute(
            select(models.Group).where(models.Group.id == idol_data.group_id)
        ).scalar_one()
    slugs = db.execute(select(models.Idol.slug)).scalars().all()
    new_slug = slugify(idol_data.stage_name, slugs)
    new_idol.slug = new_slug
    db.add(new_idol)
    db.commit()
    db.refresh(new_idol)
    return new_idol


@router.patch("/{idol_id}", response_model=IdolResponse)
def update_idol(
    idol_id: int,
    idol_data: IdolUpdate,
    db: Session = Depends(get_db),
):
    # add rbac a bit later
    idol = db.execute(
        select(models.Idol).where(models.Idol.id == idol_id)
    ).scalar_one_or_none()
    if not idol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idol not found!",
        )
    # we write the same line soo many times, can't we just use a helper func?
    if idol_data.stage_name and idol_data.group_id:
        # check if same name from same group already exists
        idol_exists = db.execute(
            select(models.Idol).where(
                models.Idol.stage_name == idol_data.stage_name,
                models.Idol.group_id == idol_data.group_id,
                models.Idol.id != idol_id,
            )
        ).scalar_one_or_none()
        if idol_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idol from same group with same stage name already exists!",
            )

    updated_data = idol_data.model_dump(
        exclude_unset=True
    )  # dont take the keys which aren't sent from frontend
    for key, val in updated_data.items():
        setattr(idol, key, val)

    if idol_data.stage_name:
        slugs = (
            db.execute(select(models.Idol.slug).where(models.Idol.id != idol_id))
            .scalars()
            .all()
        )
        new_slug = slugify(idol_data.stage_name, slugs)
        idol.slug = new_slug

    db.commit()
    db.refresh(idol)
    return idol


@router.delete("/{idol_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_idol(idol_id: int, db: Session = Depends(get_db)):
    idol = db.execute(
        select(models.Idol).where(models.Idol.id == idol_id)
    ).scalar_one_or_none()
    if not idol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idol Not found!",
        )
    db.delete(idol)
    db.commit()
