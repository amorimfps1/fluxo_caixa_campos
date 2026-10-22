import os
import urllib.parse

from configuracao import carregar_configuracao
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

carregar_configuracao()


def normalizar_database_url(raw_url: str) -> str:
    """Normaliza e escapa a URL do banco para conexões SQLAlchemy seguras.
    
    Corrige acidentais '@@' e codifica caracteres especiais na senha.
    """
    if not raw_url:
        return raw_url
    raw_url = raw_url.strip()
    if "@" not in raw_url or "://" not in raw_url:
        return raw_url

    scheme, _, rest = raw_url.partition("://")
    user_pass_part, _, host_part = rest.rpartition("@")
    host_part = host_part.lstrip("@")

    if ":" in user_pass_part:
        user, _, raw_pass = user_pass_part.partition(":")
        unquoted_pass = urllib.parse.unquote(raw_pass)
        encoded_pass = urllib.parse.quote_plus(unquoted_pass)
        return f"{scheme}://{user}:{encoded_pass}@{host_part}"

    return f"{scheme}://{user_pass_part}@{host_part}"


DATABASE_URL = normalizar_database_url(os.getenv("DATABASE_URL", ""))

if not DATABASE_URL:
    raise RuntimeError(
        "A variável DATABASE_URL não está configurada. "
        "Defina-a no arquivo .env ou no ambiente."
    )

engine_kwargs = {}
if DATABASE_URL.startswith("mysql"):
    engine_kwargs.update({"pool_pre_ping": True, "pool_recycle": 3600})
    if "tidbcloud.com" in DATABASE_URL or os.getenv("DB_SSL", "").lower() in ("true", "1"):
        import ssl
        engine_kwargs["connect_args"] = {"ssl": ssl.create_default_context()}

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
