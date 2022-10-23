"""create students

Revision ID: 0a5c3c5ca317
Revises: 05b3e33b734a
Create Date: 2022-10-23 15:22:09.028999

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a5c3c5ca317'
down_revision = '05b3e33b734a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'students',
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
    )


def downgrade():
    op.drop_table('students')
