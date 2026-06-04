import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel
from testcontainers.postgres import PostgresContainer

from app.database import get_session
from app.main import app


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine", driver="psycopg2") as container:
        yield container


@pytest.fixture(scope="session")
def engine(postgres_container: PostgresContainer):
    return create_engine(postgres_container.get_connection_url())


@pytest.fixture(autouse=True)
def setup_tables(engine):
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def session(engine, setup_tables):
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
