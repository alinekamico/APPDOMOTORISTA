"""observacao no evento de entrega

Revision ID: 7f443adfe6ed
Revises: 7375905d3d73
Create Date: 2026-08-04 16:14:40.718210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f443adfe6ed'
down_revision: Union[str, Sequence[str], None] = '7375905d3d73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("eventos_entrega") as batch_op:
        batch_op.add_column(sa.Column("observacao", sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("eventos_entrega") as batch_op:
        batch_op.drop_column("observacao")
