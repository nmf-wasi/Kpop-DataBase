from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.routers import users, idols, songs, groups, albums
from app.database.database import get_db
from app.middleware.rate_limiter import rate_limiter
from app.config.config import settings
app = FastAPI()

if not settings.TESTING:
    app.middleware("http")(rate_limiter)
# registers a middleware for the HTTP protocol, Calling it with (rate_limiter) immediately after is Python's decorator mechanics applied manually
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(idols.router, prefix="/api/idols", tags=["idols"])
app.include_router(songs.router, prefix="/api/songs", tags=["songs"])
app.include_router(groups.router, prefix="/api/groups", tags=["groups"])
app.include_router(albums.router, prefix="/api/albums", tags=["albums"])


@app.get("/")
def home(dh: Session = Depends(get_db)):
    return {"Author": "Wasi"}


for f in ["users", "idols", "songs", "groups", "albums"]:
    print(f"app.include_router({f}.router, prefix='/api/{f}', tags=['{f}'])")
