"""Script de Inicialização e Migração para o Supabase (PostgreSQL).

Funcionalidades:
1. Aplica o schema completo no Supabase (tabelas, enums, chaves estrangeiras, índices e categorias).
2. Opcionalmente migra todos os dados de uma base MySQL existente para o Supabase.
3. Atualiza as sequences de autoincrement (SERIAL) para evitar conflitos de ID.
4. Valida a conexão e integridade dos dados.

Uso:
    python scripts/migrar_para_supabase.py
    OU passando variáveis no ambiente ou arquivo .env:
    SUPABASE_URL="postgresql+psycopg2://postgres.xxxx:yyyy@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
    MYSQL_URL="mysql+pymysql://user:pass@host/db"
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz e backend ao sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

from sqlalchemy import create_engine, text, inspect
from database import normalizar_database_url


TABELAS_ORDEM = [
    "usuarios",
    "tentativas_login",
    "categorias_movimentacao",
    "contas_bancarias",
    "fluxo_dinheiro",
    "calculos_financeiros",
    "metas_financeiras",
    "orcamentos",
    "preferencias_alerta",
    "alertas_lidos",
]

TABELAS_COM_ID_SERIAL = [
    "usuarios",
    "contas_bancarias",
    "fluxo_dinheiro",
    "calculos_financeiros",
    "metas_financeiras",
    "orcamentos",
]


def obter_url_supabase() -> str:
    url = os.getenv("SUPABASE_DATABASE_URL") or os.getenv("SUPABASE_URL")
    if not url:
        db_url = os.getenv("DATABASE_URL", "")
        if "supabase" in db_url or "postgres" in db_url:
            url = db_url

    if not url:
        print("\n=== CONFIGURAÇÃO DO SUPABASE ===")
        print("Informe a Connection String do Supabase (URI):")
        print("Exemplo: postgresql://postgres.xxxx:sua_senha@aws-0-sa-east-1.pooler.supabase.com:6543/postgres")
        url = input("URL Supabase: ").strip()

    if not url:
        print("[ERRO] Nenhuma URL do Supabase informada. Abortando.")
        sys.exit(1)

    return normalizar_database_url(url)


def obter_url_mysql() -> str:
    url = os.getenv("MYSQL_DATABASE_URL") or os.getenv("MYSQL_URL")
    if not url:
        db_url = os.getenv("DATABASE_URL", "")
        if db_url.startswith("mysql"):
            url = db_url
    return normalizar_database_url(url) if url else ""


def aplicar_schema_supabase(engine_pg):
    print("\n[1/3] Aplicando schema e tabelas no Supabase...")
    caminho_sql = BASE_DIR / "scripts" / "supabase_schema_completo.sql"
    if not caminho_sql.exists():
        print(f"[ERRO] Arquivo SQL não encontrado em: {caminho_sql}")
        sys.exit(1)

    conteudo_sql = caminho_sql.read_text(encoding="utf-8")

    with engine_pg.connect() as conn:
        with conn.begin():
            # Executa o script completo em um bloco
            conn.execute(text(conteudo_sql))
    print("  -> Schema, tabelas, enums e categorias base criados com sucesso!")


def atualizar_sequences(engine_pg):
    print("\n[3/3] Sincronizando sequências SERIAL no PostgreSQL...")
    with engine_pg.connect() as conn:
        with conn.begin():
            for tabela in TABELAS_COM_ID_SERIAL:
                try:
                    sql = text(f"""
                        SELECT setval(
                            pg_get_serial_sequence('{tabela}', 'id'),
                            COALESCE((SELECT MAX(id) FROM {tabela}), 1)
                        );
                    """)
                    conn.execute(sql)
                    print(f"  -> Sequência da tabela '{tabela}' sincronizada.")
                except Exception as e:
                    print(f"  [AVISO] Não foi possível atualizar sequência de '{tabela}': {e}")


def migrar_dados(engine_mysql, engine_pg):
    print("\n[2/3] Migrando dados do MySQL para o Supabase...")
    insp_mysql = inspect(engine_mysql)
    tabelas_mysql = set(insp_mysql.get_table_names())

    with engine_mysql.connect() as conn_mysql, engine_pg.connect() as conn_pg:
        for tabela in TABELAS_ORDEM:
            if tabela not in tabelas_mysql:
                print(f"  -> Tabela '{tabela}' não existe no MySQL de origem. Pulando.")
                continue

            # Lê todos os registros do MySQL
            result = conn_mysql.execute(text(f"SELECT * FROM {tabela}"))
            linhas = [dict(row._mapping) for row in result]
            if not linhas:
                print(f"  -> Tabela '{tabela}': 0 registros encontrados.")
                continue

            print(f"  -> Migrando {len(linhas)} registro(s) para '{tabela}'...")

            # Colunas da tabela de destino
            insp_pg = inspect(engine_pg)
            colunas_pg = {c["name"] for c in insp_pg.get_columns(tabela)}

            with conn_pg.begin():
                for linha in linhas:
                    # Filtra apenas colunas existentes no destino
                    dados_filtrados = {k: v for k, v in linha.items() if k in colunas_pg}
                    colunas_str = ", ".join(dados_filtrados.keys())
                    params_str = ", ".join(f":{k}" for k in dados_filtrados.keys())

                    if tabela == "categorias_movimentacao":
                        sql = text(f"INSERT INTO {tabela} ({colunas_str}) VALUES ({params_str}) ON CONFLICT (nome) DO NOTHING")
                    elif tabela == "usuarios":
                        sql = text(f"INSERT INTO {tabela} ({colunas_str}) VALUES ({params_str}) ON CONFLICT (id) DO NOTHING")
                    elif tabela == "tentativas_login":
                        sql = text(f"INSERT INTO {tabela} ({colunas_str}) VALUES ({params_str}) ON CONFLICT (chave_cliente) DO NOTHING")
                    elif tabela in TABELAS_COM_ID_SERIAL:
                        sql = text(f"INSERT INTO {tabela} ({colunas_str}) VALUES ({params_str}) ON CONFLICT (id) DO NOTHING")
                    else:
                        sql = text(f"INSERT INTO {tabela} ({colunas_str}) VALUES ({params_str})")

                    conn_pg.execute(sql, dados_filtrados)


def validar_supabase(engine_pg):
    print("\n=== RESUMO DAS TABELAS NO SUPABASE ===")
    with engine_pg.connect() as conn:
        for tabela in TABELAS_ORDEM:
            try:
                qtd = conn.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar()
                print(f"  - {tabela}: {qtd} registro(s)")
            except Exception as e:
                print(f"  - {tabela}: ERRO ao consultar ({e})")


def main():
    print("=" * 65)
    print("   FLUXO DE CAIXA - MIGRAÇÃO PARA SUPABASE (POSTGRESQL)")
    print("=" * 65)

    url_supabase = obter_url_supabase()
    print(f"\nSupabase URL configurada: {url_supabase.split('@')[-1] if '@' in url_supabase else '...'}")

    engine_pg = create_engine(
        url_supabase,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"}
    )

    # 1. Aplica o schema
    aplicar_schema_supabase(engine_pg)

    # 2. Opcional: Migração de dados do MySQL
    url_mysql = obter_url_mysql()
    migrar = False
    if url_mysql:
        print(f"\nBase MySQL detectada: {url_mysql.split('@')[-1] if '@' in url_mysql else '...'}")
        resposta = input("Deseja copiar os dados existentes do MySQL para o Supabase? (s/N): ").strip().lower()
        migrar = resposta in ("s", "sim", "y", "yes")

    if migrar:
        engine_mysql = create_engine(url_mysql, pool_pre_ping=True)
        migrar_dados(engine_mysql, engine_pg)

    # 3. Atualiza sequences
    atualizar_sequences(engine_pg)

    # 4. Validação final
    validar_supabase(engine_pg)

    print("\n" + "=" * 65)
    print(" Migração para o Supabase concluída com sucesso!")
    print(" Atualize a variável DATABASE_URL no seu ambiente / Render:")
    print(f" DATABASE_URL={url_supabase}")
    print("=" * 65)


if __name__ == "__main__":
    main()
