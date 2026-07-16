from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
