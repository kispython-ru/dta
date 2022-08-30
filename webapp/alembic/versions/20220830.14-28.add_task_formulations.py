"""add task formulations

Revision ID: 05b3e33b734a
Revises: 1ad068c58869
Create Date: 2022-08-30 14:28:53.466801

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05b3e33b734a'
down_revision = '1ad068c58869'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("formulation", sa.String, nullable=True))


def downgrade():
    op.drop_column("tasks", "formulation")
