from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.database import get_db
from app.models import models
router = APIRouter()


@router.get("/")
def get_idols(db:Session=Depends(get_db)):
    return db.execute(select(models.Idol)).scalars().all()

