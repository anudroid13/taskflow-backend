import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_secret = os.getenv("SECRET_KEY", "")
if not _secret or _secret == "changeme":
    logger.warning("SECRET_KEY is not set or using default 'changeme'. Set a strong secret in production.")
    _secret = _secret or "changeme"

class Settings:
    SECRET_KEY: str = _secret
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    CORS_ORIGINS: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

settings = Settings()
