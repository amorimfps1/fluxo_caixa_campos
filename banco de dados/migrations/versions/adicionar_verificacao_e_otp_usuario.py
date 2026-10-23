"""Adiciona campos de verificação de e-mail e código OTP temporário ao usuário."""
from alembic import op
import sqlalchemy as sa


revision = "verificacao_otp_usuario"
down_revision = "adicionar_telefone_usuario"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column(
            "email_verificado",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "usuarios",
        sa.Column(
            "codigo_verificacao_hash",
            sa.String(length=64),
            nullable=True,
        ),
    )
    op.add_column(
        "usuarios",
        sa.Column(
            "codigo_expira_em",
            sa.DateTime(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("usuarios", "codigo_expira_em")
    op.drop_column("usuarios", "codigo_verificacao_hash")
    op.drop_column("usuarios", "email_verificado")
