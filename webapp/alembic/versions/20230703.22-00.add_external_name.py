"""add_external_name

Revision ID: eeff291eb0fb
Revises: a34a5c415f31
Create Date: 2023-07-03 22:00:17.927592

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eeff291eb0fb'
down_revision = 'a34a5c415f31'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("groups", sa.Column("external", sa.String, nullable=True))


def downgrade():
    op.drop_column("groups", "external")
