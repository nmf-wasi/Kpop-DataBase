from fastapi import FastAPI, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.routers import users, idols, songs, groups, albums
from app.database.database import get_db
from app.middleware.rate_limiter import rate_limiter
from app.config.config import settings
from app.core.logging_config import setup_logging
from app.middleware.logging_middleware import logging_middleware
import logging 

setup_logging()
app = FastAPI()

app.middleware("http")(logging_middleware)


if not settings.TESTING:
    app.middleware("http")(rate_limiter)
# registers a middleware for the HTTP protocol, Calling it with (rate_limiter) immediately after is Python's decorator mechanics applied manually

@app.exception_handler(Exception)
async def global_exception_handler(request:Request, exc:Exception):
    logging.error(
        f"Unhandled errorr on {request.method} {request.url.path}: {exc}"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail":"An unexpected error occured!"}
    )

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
