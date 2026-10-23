"""Remove um usuário de teste e todos os dados associados a ele.

Uso (apenas exemplos, não execute sem confirmação):

    # Na raiz do repositório, com o ambiente virtual ativado:
    $env:DATABASE_URL = "mysql+pymysql://USUARIO:SENHA@127.0.0.1:3306/fluxo_caixa_dev"
    python scripts/remover_usuario_teste.py usuario@exemplo.com

O script lê `DATABASE_URL` do ambiente (via .env ou variável exportada).
Nenhuma credencial está fixa no código.

O que será apagado, em ordem:
1. Metas financeiras do usuário (`metas_financeiras`)
2. Cálculos financeiros consolidados das contas do usuário (`calculos_financeiros`)
3. Movimentações financeiras vinculadas às contas do usuário (`fluxo_dinheiro`)
4. Contas bancárias do usuário (`contas_bancarias`)
5. O próprio usuário (`usuarios`)

As chaves estrangeiras usam `ON DELETE CASCADE` nas migrações Alembic
(`fk_conta_usuario`, `fk_fluxo_conta`, `fk_meta_usuario`), mas a exclusão
é feita tabela por tabela para mostrar exatamente o que será removido
antes de confirmar.

A tabela `tentativas_login` não é apagada pelo script: sua chave é
`chave_tentativa` (hash SHA-256 do IP/conta), não o id do usuário, e
não há chave estrangeira para `usuarios.id`.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
for caminho in (ROOT, BACKEND_DIR):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))

from configuracao import carregar_configuracao
from database import DATABASE_URL, SessionLocal
from models import Usuario
from sqlalchemy import text
from sqlalchemy.engine import make_url

carregar_configuracao()


def contar_registros(session, usuario_id):
    """Retorna um dicionário com a quantidade de registros por tabela."""
    tabelas = {
        "metas_financeiras": (
            "SELECT COUNT(*) FROM metas_financeiras WHERE usuario_id = :uid"
        ),
        "calculos_financeiros": (
            "SELECT COUNT(*) FROM calculos_financeiros WHERE conta_bancaria_id IN "
            "(SELECT id FROM contas_bancarias WHERE usuario_id = :uid)"
        ),
        "fluxo_dinheiro": (
            "SELECT COUNT(*) FROM fluxo_dinheiro WHERE conta_bancaria_id IN "
            "(SELECT id FROM contas_bancarias WHERE usuario_id = :uid)"
        ),
        "contas_bancarias": (
            "SELECT COUNT(*) FROM contas_bancarias WHERE usuario_id = :uid"
        ),
        "usuarios": (
            "SELECT COUNT(*) FROM usuarios WHERE id = :uid"
        ),
    }
    resultado = {}
    for nome, sql in tabelas.items():
        resultado[nome] = session.execute(text(sql), {"uid": usuario_id}).scalar()
    return resultado


def exibir_resumo(session, usuario):
    """Mostra os dados que serão apagados e pede confirmação."""
    usuario_id = usuario.id
    contagens = contar_registros(session, usuario_id)

    print("\n=== Usuário encontrado ===")
    print(f"ID:              {usuario_id}")
    print(f"E-mail:          {usuario.email}")
    print(f"Nome completo:   {usuario.nome_completo}")
    print(f"Criado em:       {usuario.criado_em}")
    print(f"Telefone:        {'(cifrado, não exibido)' if usuario.telefone else 'não informado'}")
    print()
    print("Registros que serão apagados:")
    print(f"  - Metas financeiras:      {contagens['metas_financeiras']}")
    print(f"  - Cálculos financeiros:   {contagens['calculos_financeiros']}")
    print(f"  - Movimentações:          {contagens['fluxo_dinheiro']}")
    print(f"  - Contas bancárias:       {contagens['contas_bancarias']}")
    print(f"  - Usuário:                {contagens['usuarios']}")
    print()
    print("ATENÇÃO: esta ação é irreversível. Todos os dados acima serão excluídos.")
    print()


def remover_usuario(session, usuario_id):
    """Executa a exclusão em ordem segura, em uma única transação."""
    try:
        # 1. Metas financeiras
        session.execute(
            text("DELETE FROM metas_financeiras WHERE usuario_id = :uid"),
            {"uid": usuario_id},
        )
        # 2. Cálculos financeiros vinculados às contas do usuário
        session.execute(
            text(
                "DELETE FROM calculos_financeiros WHERE conta_bancaria_id IN "
                "(SELECT id FROM contas_bancarias WHERE usuario_id = :uid)"
            ),
            {"uid": usuario_id},
        )
        # 3. Movimentações financeiras (portável: subquery em vez de JOIN)
        session.execute(
            text(
                "DELETE FROM fluxo_dinheiro WHERE conta_bancaria_id IN "
                "(SELECT id FROM contas_bancarias WHERE usuario_id = :uid)"
            ),
            {"uid": usuario_id},
        )
        # 4. Contas bancárias
        session.execute(
            text("DELETE FROM contas_bancarias WHERE usuario_id = :uid"),
            {"uid": usuario_id},
        )
        # 5. Usuário
        session.execute(
            text("DELETE FROM usuarios WHERE id = :uid"),
            {"uid": usuario_id},
        )
        session.commit()
    except Exception:
        session.rollback()
        raise


def main():
    if len(sys.argv) != 2:
        print("Uso: python scripts/remover_usuario_teste.py <email>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    if not email:
        print("E-mail inválido.")
        sys.exit(1)

    session = SessionLocal()
    try:
        usuario = session.query(Usuario).filter_by(email=email).first()

        if not usuario:
            print(f"Nenhum usuário encontrado com o e-mail: {email}")
            sys.exit(0)

        nome_banco = make_url(DATABASE_URL).database if DATABASE_URL else None

        print("\n=== Banco de dados alvo ===")
        print(
            f"DATABASE_URL: {make_url(DATABASE_URL).render_as_string(hide_password=True) if DATABASE_URL else '(não definida)'}"
        )
        print(f"Nome do schema/banco: {nome_banco or '<não especificado>'}")
        print()

        exibir_resumo(session, usuario)

        confirmacao_banco = input(
            f"Confirme o nome do banco/schema para prosseguir ({nome_banco}): "
        ).strip()
        if confirmacao_banco != nome_banco:
            print("Nome do banco não confere. Operação cancelada.")
            sys.exit(0)

        confirmacao = input(
            "Digite CONFIRMO para apagar o usuário e todos os dados associados: "
        ).strip()
        if confirmacao != "CONFIRMO":
            print("Operação cancelada pelo usuário.")
            sys.exit(0)

        remover_usuario(session, usuario.id)
        print(f"\nUsuário {email} (ID {usuario.id}) e todos os dados associados foram removidos.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
