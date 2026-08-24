from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config.config import settings

engine = create_engine(settings.DATABASE_URL)
connect_args = {"check_same_thread": False}

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


class Base(DeclarativeBase):
    """every model on ths project inherit from this model"""

    pass


def get_db():
    """fast api dependency, yields a db session for the duration of one request and then closes it"""

    with SessionLocal() as db:
        yield db
