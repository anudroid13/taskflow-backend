from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Import all model modules to register them with SQLAlchemy
from app.models import user, task, attachment