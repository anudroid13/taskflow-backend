import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserRead, UserSignup, LoginRequest
from app.crud import user as crud_user
from app.core import security
from app.db.session import get_db

logger = logging.getLogger(__name__)

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
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = security.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        logger.warning("Failed login attempt for email: %s", login_data.email)
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = security.create_access_token(data={"sub": str(user.id)})
    logger.info("User logged in: %s (id=%d)", user.email, user.id)
    return {"access_token": access_token, "token_type": "bearer"}
