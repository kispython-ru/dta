"""create_type_of_task

Revision ID: 3782564289c1
Revises: fe6046af9ed9
Create Date: 2025-06-02 15:41:41.502795

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3782564289c1'
down_revision = 'fe6046af9ed9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("type", sa.Integer, nullable=False, server_default='0'))


def downgrade():
    op.drop_column("tasks", "type")
