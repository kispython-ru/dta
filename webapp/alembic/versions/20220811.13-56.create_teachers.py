"""create teachers

Revision ID: 1ad068c58869
Revises: 1333575b4d28
Create Date: 2022-08-11 13:56:38.719540

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ad068c58869'
down_revision = '1333575b4d28'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'teachers',
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("login", sa.String, nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
    )


def downgrade():
    op.drop_table('teachers')
