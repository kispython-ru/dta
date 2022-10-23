"""create mailers

Revision ID: b9601eedb390
Revises: 0a5c3c5ca317
Create Date: 2022-10-23 15:23:13.033873

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9601eedb390'
down_revision = '0a5c3c5ca317'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'mailers',
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("domain", sa.String, nullable=False)
    )


def downgrade():
    op.drop_table('mailers')
