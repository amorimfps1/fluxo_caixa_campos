import os

from configuracao import carregar_configuracao
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

carregar_configuracao()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "A variável DATABASE_URL não está configurada. "
        "Defina-a no arquivo .env ou no ambiente."
    )

engine_kwargs = {}
if DATABASE_URL.startswith("mysql"):
    engine_kwargs.update({"pool_pre_ping": True, "pool_recycle": 3600})

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()