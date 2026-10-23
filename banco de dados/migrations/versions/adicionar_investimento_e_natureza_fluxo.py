"""Adiciona classificacao de conta fixa/variavel e tipo de ativo de investimento ao fluxo."""
from alembic import op
import sqlalchemy as sa


revision = "investimento_e_natureza"
down_revision = "verificacao_otp_usuario"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "fluxo_dinheiro",
        sa.Column(
            "natureza_conta",
            sa.Enum("fixa", "variavel"),
            nullable=True,
        ),
    )
    op.add_column(
        "fluxo_dinheiro",
        sa.Column(
            "tipo_investimento",
            sa.String(length=60),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("fluxo_dinheiro", "tipo_investimento")
    op.drop_column("fluxo_dinheiro", "natureza_conta")
