from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all model modules to register them with SQLAlchemy
from app.models import user, task, attachment