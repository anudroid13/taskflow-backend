import logging
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.api.v1.routers import auth, tasks, attachment, user, dashboard
from app.db.base import Base
from app.db.session import engine, get_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="TaskFlow API")

Base.metadata.create_all(bind=engine)

app.include_router(auth.router) 
app.include_router(tasks.router)
app.include_router(attachment.router)
app.include_router(user.router)
app.include_router(dashboard.router)

@app.get("/")
def read_root():
    return {"message": "TaskFlow API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error("Health check failed: %s", e)
        return {"status": "unhealthy", "database": "disconnected"}