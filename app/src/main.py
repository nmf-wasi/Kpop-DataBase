from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.routers import users, idols
from app.database.database import get_db

app = FastAPI()

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(idols.router, prefix="/api/idols", tags=["kpop"])


@app.get("/")
def home(dh: Session = Depends(get_db)):
    return {"Author": "Wasi"}
