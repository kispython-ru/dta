"""add blocked to students

Revision ID: 0deb2448be12
Revises: e147c0fe4f60
Create Date: 2022-11-06 21:55:33.207993

"""
from alembic import op
from alembic.operations.batch import BatchOperationsImpl
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0deb2448be12'
down_revision = 'e147c0fe4f60'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("students", sa.Column("blocked", sa.Boolean, nullable=True))
    op.execute("update students set blocked = false")
    bop: BatchOperationsImpl
    with op.batch_alter_table("students") as bop:
        bop.alter_column("blocked", nullable=False)


def downgrade():
    op.drop_column("students", "blocked")
