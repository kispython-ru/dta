"""

Revision ID: 30b579748cec
Revises: eeff291eb0fb
Create Date: 2024-02-29 01:04:59.268423

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30b579748cec'
down_revision = 'eeff291eb0fb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("messages", sa.Column("session_id", sa.String, nullable=True))


def downgrade():
    op.drop_column("messages", "session_id")
