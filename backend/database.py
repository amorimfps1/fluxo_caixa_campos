import os
import urllib.parse

from configuracao import carregar_configuracao
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

carregar_configuracao()


def normalizar_database_url(raw_url: str) -> str:
    """Normaliza e escapa a URL do banco para conexões SQLAlchemy seguras.
    
    1. Garante o dialeto mysql+pymysql caso o usuário informe apenas mysql://.
    2. Garante o banco gravável '/test' caso venha apontando para o sistema '/sys'.
    3. Remove parâmetros de SSL da query string para evitar conflito com connect_args.
    4. Corrige acidentais '@@' e sanitiza o host.
    5. Codifica caracteres especiais na senha via quote_plus.
    """
    if not raw_url:
        return raw_url
    raw_url = raw_url.strip()
    if "://" not in raw_url:
        return raw_url

    scheme, _, rest = raw_url.partition("://")
    if scheme == "mysql":
        scheme = "mysql+pymysql"

    if "@" not in rest:
        return f"{scheme}://{rest}"

    user_pass_part, _, host_part = rest.rpartition("@")
    host_part = host_part.lstrip("@")

    # Impede o uso da base reservada do sistema 'sys'
    if host_part.endswith("/sys") or host_part.split("?")[0].endswith("/sys"):
        host_part = host_part.replace("/sys", "/test", 1)

    # Remove parâmetros de SSL da query string para passar via connect_args
    if "?" in host_part:
        base_host, _, query = host_part.partition("?")
        params = [
            p for p in query.split("&")
            if not p.lower().startswith("ssl_") and not p.lower().startswith("ssl=")
        ]
        host_part = base_host + (("?" + "&".join(params)) if params else "")

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
        import certifi
        ca_candidates = [
            os.getenv("CA_PATH", ""),
            "/etc/secrets/tidb_ca.pem",
            "/etc/ssl/certs/ca-certificates.crt",
            certifi.where()
        ]
        ca_path = next((p for p in ca_candidates if p and os.path.exists(p)), certifi.where())
        engine_kwargs["connect_args"] = {"ssl": {"ca": ca_path}}

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
