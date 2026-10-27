"""Adiciona tipo investimento ao enum de tipo em fluxo_dinheiro.

Revision ID: adicionar_tipo_investimento
Revises: adicionar_dia_repeticao
Create Date: 2026-10-27 09:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "adicionar_tipo_investimento"
down_revision: Union[str, None] = "adicionar_dia_repeticao"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        op.execute(
            sa.text(
                "ALTER TABLE fluxo_dinheiro MODIFY COLUMN tipo "
                "ENUM('entrada', 'saida', 'transferencia', 'ajuste', 'investimento') NOT NULL"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        op.execute(
            sa.text(
                "ALTER TABLE fluxo_dinheiro MODIFY COLUMN tipo "
                "ENUM('entrada', 'saida', 'transferencia', 'ajuste') NOT NULL"
            )
        )
