"""add ip to statuses

Revision ID: 41afa0763cca
Revises: 0df7d731072d
Create Date: 2022-06-02 13:33:25.061618

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '41afa0763cca'
down_revision = '0df7d731072d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("task_statuses", sa.Column("ip", sa.String, nullable=True))


def downgrade():
    op.drop_column("task_statuses", "ip")
