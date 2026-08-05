"""romaneio origem para clonagem de pendentes

Revision ID: 72796ce424eb
Revises: 7f443adfe6ed
Create Date: 2026-08-05 10:33:27.373069

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72796ce424eb'
down_revision: Union[str, Sequence[str], None] = '7f443adfe6ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("romaneios") as batch_op:
        batch_op.add_column(sa.Column("romaneio_origem_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_romaneios_romaneio_origem_id", "romaneios", ["romaneio_origem_id"], ["id"]
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("romaneios") as batch_op:
        batch_op.drop_constraint("fk_romaneios_romaneio_origem_id", type_="foreignkey")
        batch_op.drop_column("romaneio_origem_id")
