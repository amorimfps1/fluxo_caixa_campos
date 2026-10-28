"""Adiciona orçamentos e preferências/estado dos alertas."""
from alembic import op
import sqlalchemy as sa

revision = "orcamentos_alertas_supabase"
down_revision = "schema_unificado_supabase"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("orcamentos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("categoria", sa.String(100), sa.ForeignKey("categorias_movimentacao.nome"), nullable=False),
        sa.Column("mes", sa.Date, nullable=False),
        sa.Column("limite", sa.Numeric(12, 2), nullable=False),
        sa.UniqueConstraint("usuario_id", "categoria", "mes", name="uq_orcamento_usuario_categoria_mes"))
    op.create_table("preferencias_alerta",
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("orcamento", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("vencimento", sa.Boolean, nullable=False, server_default=sa.true()))
    op.create_table("alertas_lidos",
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("chave", sa.String(100), primary_key=True))

def downgrade():
    op.drop_table("alertas_lidos")
    op.drop_table("preferencias_alerta")
    op.drop_table("orcamentos")

