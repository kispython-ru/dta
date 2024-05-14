"""

Revision ID: 0ed9e0bfabcb
Revises: 30b579748cec
Create Date: 2024-05-14 22:12:06.014972

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ed9e0bfabcb'
down_revision = '30b579748cec'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("students", sa.Column("teacher", sa.Boolean, nullable=True))
    op.drop_table("teachers")


def downgrade():
    op.drop_column("students", "teacher")
    op.create_table(
        'teachers',
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("login", sa.String, nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
    )
