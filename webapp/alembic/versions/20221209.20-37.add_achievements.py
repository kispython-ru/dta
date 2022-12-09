"""add achievements

Revision ID: d0b74bb47a5d
Revises: 0deb2448be12
Create Date: 2022-12-09 20:37:42.272834

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd0b74bb47a5d'
down_revision = '0deb2448be12'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("task_statuses", sa.Column("achievements", sa.String, nullable=True))


def downgrade():
    op.drop_column("task_statuses", "achievements")
