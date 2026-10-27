"""Schema unificado para Supabase (PostgreSQL).

Cria todas as tabelas do sistema Fluxo de Caixa com todos os campos
atualizados, incluindo suporte a investimentos, classificacao de contas
fixas/variaveis e agendamento inteligente.

Esta migration e' independente (down_revision=None) pois representa o
estado completo do schema para um banco novo (Supabase).

Compatibilidade: MySQL e PostgreSQL.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "schema_unificado_supabase"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nome_completo", sa.String(length=150), nullable=False),
        sa.Column("cpf", sa.String(length=255), nullable=False),
        sa.Column("cpf_indice", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("telefone", sa.String(length=255), nullable=True),
        sa.Column(
            "email_verificado",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("codigo_verificacao_hash", sa.String(length=64), nullable=True),
        sa.Column("codigo_expira_em", sa.DateTime(), nullable=True),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("cpf", name="uq_usuarios_cpf"),
        sa.UniqueConstraint("email", name="uq_usuarios_email"),
        sa.UniqueConstraint("cpf_indice", name="uq_usuarios_cpf_indice"),
    )

    op.create_table(
        "tentativas_login",
        sa.Column("chave_cliente", sa.String(length=64), primary_key=True),
        sa.Column("tentativas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inicio_janela", sa.DateTime(), nullable=False),
        sa.Column("bloqueado_ate", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "idx_tentativas_login_janela", "tentativas_login", ["inicio_janela"]
    )

    op.create_table(
        "categorias_movimentacao",
        sa.Column("nome", sa.String(length=100), primary_key=True),
    )

    op.create_table(
        "contas_bancarias",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("nome_banco", sa.String(length=100), nullable=False),
        sa.Column(
            "tipo_conta",
            sa.Enum(
                "corrente", "poupanca", "investimento", name="tipo_conta_enum"
            ),
            nullable=False,
        ),
        sa.Column(
            "valor_conta_atual",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("ativa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "criado_em",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name="fk_conta_usuario",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )
    op.create_index(
        "idx_contas_usuario", "contas_bancarias", ["usuario_id"]
    )

    op.create_table(
        "fluxo_dinheiro",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("conta_bancaria_id", sa.Integer(), nullable=False),
        sa.Column("conta_destino_id", sa.Integer(), nullable=True),
        sa.Column("descricao", sa.String(length=200), nullable=False),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum(
                "entrada", "saida", "transferencia",
                "ajuste", "investimento",
                name="tipo_movimentacao_enum",
            ),
            nullable=False,
        ),
        sa.Column("categoria", sa.String(length=100), nullable=False),
        sa.Column("data_movimentacao", sa.Date(), nullable=False),
        sa.Column("observacao", sa.String(length=255), nullable=True),
        sa.Column("transferencia_id", sa.String(length=36), nullable=True),
        sa.Column(
            "transferencia_direcao",
            sa.Enum(
                "origem", "destino",
                name="direcao_transferencia_enum",
            ),
            nullable=True,
        ),
        sa.Column("natureza_conta", sa.String(length=20), nullable=True),
        sa.Column("dia_repeticao", sa.Integer(), nullable=True),
        sa.Column("tipo_investimento", sa.String(length=60), nullable=True),
        sa.ForeignKeyConstraint(
            ["conta_bancaria_id"],
            ["contas_bancarias.id"],
            name="fk_fluxo_conta",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["conta_destino_id"],
            ["contas_bancarias.id"],
            name="fk_fluxo_conta_destino",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["categoria"],
            ["categorias_movimentacao.nome"],
            name="fk_fluxo_categoria",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
    )
    op.create_index("idx_fluxo_conta", "fluxo_dinheiro", ["conta_bancaria_id"])
    op.create_index(
        "idx_fluxo_data", "fluxo_dinheiro", ["data_movimentacao"]
    )
    op.create_index("idx_fluxo_tipo", "fluxo_dinheiro", ["tipo"])
    op.create_index(
        "ix_fluxo_dinheiro_transferencia_id",
        "fluxo_dinheiro",
        ["transferencia_id"],
    )

    op.create_table(
        "calculos_financeiros",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("conta_bancaria_id", sa.Integer(), nullable=False),
        sa.Column(
            "tipo_calculo",
            sa.Enum(
                "diario", "semanal", "mensal", "anual",
                name="tipo_calculo_enum",
            ),
            nullable=False,
        ),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=False),
        sa.Column(
            "valor_original",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "total_entradas",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "total_saidas",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "total_investimentos",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "total_transferencias_recebidas",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "total_transferencias_enviadas",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "total_ajustes",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "valor_final",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["conta_bancaria_id"],
            ["contas_bancarias.id"],
            name="fk_calculo_conta",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )
    op.create_index(
        "idx_calculo_conta", "calculos_financeiros", ["conta_bancaria_id"]
    )

    op.create_table(
        "metas_financeiras",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("valor_meta", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "valor_atual",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_limite", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "em_andamento",
                "concluida",
                "cancelada",
                name="status_meta_enum",
            ),
            nullable=False,
            server_default="em_andamento",
        ),
        sa.Column("descricao", sa.String(length=255), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name="fk_meta_usuario",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )
    op.create_index(
        "idx_metas_usuario", "metas_financeiras", ["usuario_id"]
    )

    op.execute(
        sa.text(
            "INSERT INTO categorias_movimentacao (nome) VALUES "
            "('alimentacao'), ('ajuste'), ('compras'), ('contas'), "
            "('educacao'), ('freelance'), ('impostos'), ('investimento'), "
            "('lazer'), ('moradia'), ('outros'), ('salario'), ('saude'), "
            "('transporte'), ('transferencia'), ('vendas') "
            "ON CONFLICT (nome) DO NOTHING"
        )
    )


def downgrade() -> None:
    op.drop_index("idx_metas_usuario", table_name="metas_financeiras")
    op.drop_table("metas_financeiras")
    op.drop_index("idx_calculo_conta", table_name="calculos_financeiros")
    op.drop_table("calculos_financeiros")
    op.drop_index("ix_fluxo_dinheiro_transferencia_id", table_name="fluxo_dinheiro")
    op.drop_index("idx_fluxo_tipo", table_name="fluxo_dinheiro")
    op.drop_index("idx_fluxo_data", table_name="fluxo_dinheiro")
    op.drop_index("idx_fluxo_conta", table_name="fluxo_dinheiro")
    op.drop_table("fluxo_dinheiro")
    op.drop_index("idx_contas_usuario", table_name="contas_bancarias")
    op.drop_table("contas_bancarias")
    op.drop_table("categorias_movimentacao")
    op.drop_index("idx_tentativas_login_janela", table_name="tentativas_login")
    op.drop_table("tentativas_login")
    op.drop_table("usuarios")
