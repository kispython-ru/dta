"""add student to messages

Revision ID: e147c0fe4f60
Revises: b9601eedb390
Create Date: 2022-11-06 21:53:37.037891

"""
from alembic import op
from alembic.operations.batch import BatchOperationsImpl
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e147c0fe4f60'
down_revision = 'b9601eedb390'
branch_labels = None
depends_on = None


def upgrade():
    bop: BatchOperationsImpl
    with op.batch_alter_table("messages") as bop:
        bop.add_column(sa.Column(
            "student",
            sa.Integer,
            sa.ForeignKey("students.id", name="student"),
            nullable=True,
        ))


def downgrade():
    op.drop_column("messages", "student")
