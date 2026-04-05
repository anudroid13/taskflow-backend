import logging
import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserRead, UserSignup, LoginRequest
from app.crud import user as crud_user
from app.core import security
from app.db.session import get_db

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter for login
_login_attempts: dict[str, list[float]] = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300  # 5 minutes
_CLEANUP_INTERVAL = 60  # seconds between full sweeps
_last_cleanup = 0.0

def _check_rate_limit(key: str):
    global _last_cleanup
    now = time.time()
    # Periodic sweep: remove stale keys to prevent unbounded growth
    if now - _last_cleanup > _CLEANUP_INTERVAL:
        stale = [k for k, v in _login_attempts.items() if all(now - t >= LOGIN_WINDOW_SECONDS for t in v)]
        for k in stale:
            del _login_attempts[k]
        _last_cleanup = now
    _login_attempts[key] = [t for t in _login_attempts[key] if now - t < LOGIN_WINDOW_SECONDS]
    if len(_login_attempts[key]) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
    _login_attempts[key].append(now)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserSignup, db: Session = Depends(get_db)):
    existing = crud_user.get_user_by_email(db, user_in.email)
    if existing:
        logger.warning("Signup attempt with existing email: %s", user_in.email)
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud_user.create_user(db, UserCreate(
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
    ))
    logger.info("New user registered: %s (id=%d)", user.email, user.id)
    return user

@router.post("/login")
def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)
    user = security.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        logger.warning("Failed login attempt for email: %s from %s", login_data.email, client_ip)
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = security.create_access_token(data={"sub": str(user.id)})
    logger.info("User logged in: %s (id=%d)", user.email, user.id)
    return {"access_token": access_token, "token_type": "bearer"}
