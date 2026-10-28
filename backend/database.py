import os
import urllib.parse
import ssl

from configuracao import carregar_configuracao
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

carregar_configuracao()


def normalizar_database_url(raw_url: str) -> str:
    """Normaliza e escapa a URL do banco para conexões SQLAlchemy seguras.
    
    1. Garante o dialeto mysql+pymysql caso o usuário informe apenas mysql://.
    2. Garante o dialeto postgresql+psycopg2 para postgres:// ou postgresql://.
    3. Garante o banco gravável '/test' caso venha apontando para o sistema '/sys'.
    4. Adiciona sslmode=require automaticamente para hosts do Supabase
       (.supabase.co ou .pooler.supabase.com) quando não especificado.
    5. Remove parâmetros de SSL da query string para evitar conflito com connect_args.
    6. Corrige acidentais '@@' e sanitiza o host.
    7. Codifica caracteres especiais na senha via quote_plus.
    """
    if not raw_url:
        return raw_url
    raw_url = raw_url.strip()
    if "://" not in raw_url:
        return raw_url

    scheme, _, rest = raw_url.partition("://")
    if scheme == "mysql":
        scheme = "mysql+pymysql"
    elif scheme in ("postgres", "postgresql"):
        scheme = "postgresql+psycopg2"

    if "@" not in rest:
        return f"{scheme}://{rest}"

    user_pass_part, _, host_part = rest.rpartition("@")
    host_part = host_part.lstrip("@")

    # Impede o uso da base reservada do sistema 'sys'
    if host_part.endswith("/sys") or host_part.split("?")[0].endswith("/sys"):
        host_part = host_part.replace("/sys", "/test", 1)

    # Adiciona sslmode=require para Supabase quando não especificado
    host_only = host_part.split("?")[0].split("/")[0]
    is_supabase = (
        ".supabase.co" in host_only or ".pooler.supabase.com" in host_only
    )
    if is_supabase:
        if "?" in host_part:
            base_host, _, query = host_part.partition("?")
            params = query.split("&")
            if not any(
                p.lower().startswith("sslmode=") for p in params
            ):
                params.append("sslmode=require")
            host_part = base_host + "?" + "&".join(params)
        else:
            host_part = host_part + "?sslmode=require"

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
        # Cria contexto SSL nativo: o PyMySQL aceita instâncias de SSLContext diretamente,
        # evitando erros de 'NO_CERTIFICATE_OR_CRL_FOUND' ao tentar ler caminhos de arquivo em Linux.
        ssl_ctx = ssl.create_default_context()
        engine_kwargs["connect_args"] = {"ssl": ssl_ctx}
elif DATABASE_URL.startswith("postgresql"):
    engine_kwargs.update({"pool_pre_ping": True, "pool_recycle": 3600})
    if ".supabase.co" in DATABASE_URL or ".pooler.supabase.com" in DATABASE_URL:
        # Supabase exige SSL para conexões externas.
        ssl_ctx = ssl.create_default_context()
        engine_kwargs["connect_args"] = {"ssl": ssl_ctx}

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


def garantir_esquema_banco() -> None:
    """Garante de forma idempotente que colunas de migrações recentes existam no banco.

    Funciona tanto com MySQL quanto PostgreSQL (Supabase).
    """
    if not DATABASE_URL:
        return
    try:
        from sqlalchemy import inspect, text

        insp = inspect(engine)
        tabelas = set(insp.get_table_names())
        dialect_name = engine.dialect.name
        with engine.begin() as conn:
            if "usuarios" in tabelas:
                cols_u = {c["name"] for c in insp.get_columns("usuarios")}
                if "email_verificado" not in cols_u:
                    if dialect_name == "postgresql":
                        conn.execute(
                            text(
                                "ALTER TABLE usuarios ADD COLUMN email_verificado BOOLEAN NOT NULL DEFAULT FALSE"
                            )
                        )
                    else:
                        conn.execute(
                            text(
                                "ALTER TABLE usuarios ADD COLUMN email_verificado BOOLEAN NOT NULL DEFAULT 0"
                            )
                        )
                if "codigo_otp" not in cols_u:
                    conn.execute(
                        text("ALTER TABLE usuarios ADD COLUMN codigo_otp VARCHAR(64) NULL")
                    )
                if "otp_expiracao" not in cols_u:
                    if dialect_name == "postgresql":
                        conn.execute(
                            text(
                                "ALTER TABLE usuarios ADD COLUMN otp_expiracao TIMESTAMP NULL"
                            )
                        )
                    else:
                        conn.execute(
                            text("ALTER TABLE usuarios ADD COLUMN otp_expiracao DATETIME NULL")
                        )
            if "fluxo_dinheiro" in tabelas:
                cols_f = {c["name"] for c in insp.get_columns("fluxo_dinheiro")}
                if "natureza_conta" not in cols_f:
                    if dialect_name == "postgresql":
                        conn.execute(
                            text(
                                "ALTER TABLE fluxo_dinheiro ADD COLUMN natureza_conta VARCHAR(20) NULL"
                            )
                        )
                    else:
                        conn.execute(
                            text(
                                "ALTER TABLE fluxo_dinheiro ADD COLUMN natureza_conta ENUM('fixa', 'variavel') NULL"
                            )
                        )
                if "dia_repeticao" not in cols_f:
                    conn.execute(
                        text("ALTER TABLE fluxo_dinheiro ADD COLUMN dia_repeticao INT NULL")
                    )
                if "tipo_investimento" not in cols_f:
                    conn.execute(
                        text("ALTER TABLE fluxo_dinheiro ADD COLUMN tipo_investimento VARCHAR(60) NULL")
                    )
                if dialect_name == "postgresql":
                    # PostgreSQL não suporta MODIFY COLUMN ENUM diretamente via ALTER TABLE simples.
                    # A coluna tipo já deve estar correta via modelos/Alembic.
                    pass
                else:
                    try:
                        conn.execute(
                            text(
                                "ALTER TABLE fluxo_dinheiro MODIFY COLUMN tipo ENUM('entrada', 'saida', 'transferencia', 'ajuste', 'investimento') NOT NULL"
                            )
                        )
                    except Exception:
                        pass

            # Garante que as tabelas de orçamentos e alertas existam de forma idempotente
            if "orcamentos" not in tabelas or "preferencias_alerta" not in tabelas or "alertas_lidos" not in tabelas:
                try:
                    from models import Orcamento, PreferenciaAlerta, AlertaLido
                    Base.metadata.create_all(
                        bind=conn,
                        tables=[Orcamento.__table__, PreferenciaAlerta.__table__, AlertaLido.__table__],
                        checkfirst=True
                    )
                except Exception:
                    pass
    except Exception:
        pass

