"""merge_orcamentos_heads

Revision ID: f24e2179202c
Revises: orcamentos_alertas_legacy, orcamentos_alertas_supabase
Create Date: 2026-10-27 22:57:42.719319
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = 'f24e2179202c'
down_revision: Union[str, None] = ('orcamentos_alertas_legacy', 'orcamentos_alertas_supabase')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
