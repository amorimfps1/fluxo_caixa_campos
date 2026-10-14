"""Add an optional encrypted phone number to each user."""
from alembic import op
import sqlalchemy as sa


revision = "adicionar_telefone_usuario"
down_revision = "proteger_cpf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("telefone", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("usuarios", "telefone")
