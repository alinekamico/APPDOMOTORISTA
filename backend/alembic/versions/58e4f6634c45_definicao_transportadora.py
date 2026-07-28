"""definicao_transportadora

Revision ID: 58e4f6634c45
Revises: 02ce8a2e13c7
Create Date: 2026-07-27 17:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58e4f6634c45'
down_revision: Union[str, Sequence[str], None] = '02ce8a2e13c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('romaneios') as batch_op:
        batch_op.alter_column('transportadora_id', existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column('transportadora_cnpj_externo', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('romaneios') as batch_op:
        batch_op.drop_column('transportadora_cnpj_externo')
        batch_op.alter_column('transportadora_id', existing_type=sa.Integer(), nullable=False)
