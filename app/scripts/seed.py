import pandas as pd
from app.models import models
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config.enums import GenderChoice
from app.database.database import SessionLocal
import re
from datetime import datetime

db = SessionLocal()


def clean(value):
    """Convert pandas NaN (emmpty CSV cell) into real None"""
    return None if pd.isna(value) else value


def slugify(text, existing_slugs: set[str]) -> str:
    """turn a name into a url-safe slug, appends -2/-3 on collision"""

    base = text.lower().strip()
    base = re.sub(r"[^a-z0-9\s-]", "", base)
    base = re.sub(r"\s+", "-", base)
    slug = base
    counter = 2
    while slug in existing_slugs:  # keep bumping until it's actually unique
        slug = f"{base}-{counter}"
        counter += 1

    existing_slugs.add(slug)
    # remember it so the *next* call sees this one too
    return slug


def create_groups(group_list: list[str], db: Session, slug_tracker: set[str]) -> None:
    print(f"Creating groups...")
    created = 0
    for name in group_list:
        existing = db.execute(
            select(models.Group).where(models.Group.name == name)
        ).scalar_one_or_none()
        if existing is not None:
            continue   # already there, skip it
        new_group = models.Group(name=name, slug=slugify(name, slug_tracker))
        db.add(new_group)
        created += 1
    db.commit()
    print(f"Created {created} new groups ({len(group_list) - created} already existed).")


def create_idols(db: Session, row: dict, slug_tracker: set[str]):

    # find group
    group_name = clean(row.get("group"))

    if group_name is None:
        group = None
    else:
        group = db.execute(
            select(models.Group).where(models.Group.name == group_name)
        ).scalar_one_or_none()
        if group is None:
            raise ValueError(f"Group '{group_name}' not found — was create_groups run first?")

    # convert str birthdate to date
    birth_date_raw = row.get("birth_date")
    birth_date = (
        datetime.strptime(birth_date_raw, "%m/%d/%Y").date()
        if pd.notna(birth_date_raw)
        else None
    )
    # convert gender from str to Enum
    gender_raw = row.get("gender")
    gender = GenderChoice(gender_raw) if pd.notna(gender_raw) else None
    # raw genders are F and M so it will work prefectly, we deliberately designed enum like that

    new_idol = models.Idol(
        stage_name=row.get("stage_name"),
        full_name=clean(row.get("full_name")),
        korean_name=clean(row.get("korean_name")),
        korean_stage_name=clean(row.get("korean_stage_name")),
        birth_date=birth_date,
        birth_place=clean(row.get("birth_place")),
        country=clean(row.get("country")),
        instagram_username=clean(row.get("instagram_username")),
        gender=gender,
        group=group,
        slug=slugify(row.get("stage_name"), slug_tracker),
    )
    db.add(new_idol)
    # no commit here. we will commit once after the whole loop


def main():
    df = pd.read_csv("./app/data/processed/kpop.csv")
    db = SessionLocal()

    try:
        group_names = sorted(df["group"].dropna().unique().tolist())
        group_slugs: set[str] = set()
        idol_slugs: set[str] = set()

        create_groups(group_list=group_names, db=db, slug_tracker=group_slugs)
        print(f"Creating {len(df)} idols...")
        for index, row in df.iterrows():
            create_idols(db=db, row=row.to_dict(), slug_tracker=idol_slugs)
        db.commit()  # one commit for all idols at once

        print("Groups and Idols created!")
    except Exception:
        db.rollback()  # if anything fails midway, undo whole batch, not a half seeded db
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
