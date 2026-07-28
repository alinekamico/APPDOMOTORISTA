"""empresa_uno_no_romaneio

Revision ID: 3c927c0c8871
Revises: 58e4f6634c45
Create Date: 2026-07-27 19:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c927c0c8871'
down_revision: Union[str, Sequence[str], None] = '58e4f6634c45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('romaneios') as batch_op:
        batch_op.add_column(sa.Column('empresa_nome', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('empresa_uf', sa.String(length=2), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('romaneios') as batch_op:
        batch_op.drop_column('empresa_uf')
        batch_op.drop_column('empresa_nome')
