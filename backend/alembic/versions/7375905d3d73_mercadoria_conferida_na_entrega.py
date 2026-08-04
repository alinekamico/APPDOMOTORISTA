"""mercadoria conferida na entrega

Revision ID: 7375905d3d73
Revises: 3c927c0c8871
Create Date: 2026-08-04 11:23:56.789396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7375905d3d73'
down_revision: Union[str, Sequence[str], None] = '3c927c0c8871'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("eventos_entrega") as batch_op:
        batch_op.add_column(sa.Column("mercadoria_conferida_na_entrega", sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("eventos_entrega") as batch_op:
        batch_op.drop_column("mercadoria_conferida_na_entrega")
