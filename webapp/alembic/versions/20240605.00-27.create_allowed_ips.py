"""create_allowed_ips

Revision ID: c9cc6ddcb46a
Revises: 0ed9e0bfabcb
Create Date: 2024-06-05 00:27:17.497763

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9cc6ddcb46a'
down_revision = '0ed9e0bfabcb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'allowed_ips',
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("ip", sa.String, nullable=False),
        sa.Column("label", sa.String, nullable=True),
    )


def downgrade():
    op.drop_table('allowed_ips')
