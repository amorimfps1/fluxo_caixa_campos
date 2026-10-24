"""Adiciona campo dia_repeticao em fluxo_dinheiro para contas fixas.

Revision ID: adicionar_dia_repeticao
Revises: investimento_e_natureza
Create Date: 2026-10-23 21:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "adicionar_dia_repeticao"
down_revision: Union[str, None] = "investimento_e_natureza"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    colunas = {col["name"] for col in inspector.get_columns("fluxo_dinheiro")}

    if "dia_repeticao" not in colunas:
        op.add_column(
            "fluxo_dinheiro",
            sa.Column("dia_repeticao", sa.Integer(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    colunas = {col["name"] for col in inspector.get_columns("fluxo_dinheiro")}

    if "dia_repeticao" in colunas:
        op.drop_column("fluxo_dinheiro", "dia_repeticao")
