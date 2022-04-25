"""add final seeds

Revision ID: 0df7d731072d
Revises: 448eb9809b1e
Create Date: 2022-04-10 02:32:17.748652

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0df7d731072d'
down_revision = '448eb9809b1e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'final_seeds',
        sa.Column("group", sa.Integer, sa.ForeignKey('groups.id'), primary_key=True, nullable=False),
        sa.Column("seed", sa.String, unique=True, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False),
    )


def downgrade():
    op.drop_table('final_seeds')
