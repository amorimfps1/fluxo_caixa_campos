import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

os.environ.update(
    {
        "DATABASE_URL": "sqlite:///:memory:",
        "APP_ENV": "development",
        "JWT_SECRET_KEY": "test-only-jwt-signing-key-do-not-use",
        "CPF_ENCRYPTION_KEY": (
            "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
        ),
    }
)

from database import Base, get_db  # noqa: E402
from models import CategoriaMovimentacao  # noqa: E402
from api import app  # noqa: E402


CATEGORIAS_FIXAS = (
    "alimentacao",
    "ajuste",
    "compras",
    "contas",
    "educacao",
    "freelance",
    "impostos",
    "investimento",
    "lazer",
    "moradia",
    "outros",
    "salario",
    "saude",
    "transporte",
    "transferencia",
    "vendas",
)


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(
        engine,
        "connect",
        lambda connection, _: connection.cursor().execute(
            "PRAGMA foreign_keys=ON"
        ),
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            CategoriaMovimentacao(nome=nome) for nome in CATEGORIAS_FIXAS
        )
        session.commit()
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    def obter_db_teste() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = obter_db_teste
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
