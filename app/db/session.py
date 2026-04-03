from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database URL from environment variable (required)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set in the .env file. "
        "Please add it: DATABASE_URL=postgresql://user:password@localhost:5432/taskflow"
    )

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)