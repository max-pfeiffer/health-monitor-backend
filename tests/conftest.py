import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.database import get_session
from app.main import app

DATABASE_URL = "sqlite://"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


@pytest.fixture(autouse=True)
def setup_tables():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def session(setup_tables):
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session: Session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
