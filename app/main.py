from fastapi import FastAPI
from app.api.v1.routers import auth, tasks, attachment, user
from app.db.base import Base
from app.db.session import engine

app = FastAPI(title="TaskFlow API")

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(attachment.router)
app.include_router(user.router)

@app.get("/")
def read_root():
    return {"message": "TaskFlow API"}