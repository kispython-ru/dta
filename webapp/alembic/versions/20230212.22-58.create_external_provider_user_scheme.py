"""Create external provider user scheme

Revision ID: 19699977434a
Revises: d0b74bb47a5d
Create Date: 2023-02-12 22:58:54.336126

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "19699977434a"
down_revision = "d0b74bb47a5d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("students", sa.Column("external_id", sa.BigInteger, nullable=True))
    op.add_column("students", sa.Column("provider", sa.String, nullable=True))
    op.add_column("students", sa.Column("group", sa.String, nullable=True))


def downgrade():
    op.drop_column("students", "external_id")
    op.drop_column("students", "provider")
    op.drop_column("students", "group")
