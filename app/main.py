from fastapi import FastAPI
from app.api.v1.routers import auth
from app.db.base import Base
from app.db.session import engine

app = FastAPI(title="TaskFlow API")

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "TaskFlow API"}