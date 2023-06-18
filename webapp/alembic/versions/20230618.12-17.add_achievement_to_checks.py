"""add_achievement_to_checks

Revision ID: a34a5c415f31
Revises: 19699977434a
Create Date: 2023-06-18 12:17:35.349319

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a34a5c415f31'
down_revision = '19699977434a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("message_checks", sa.Column("achievement", sa.Integer, nullable=True))


def downgrade():
    op.drop_column("message_checks", "achievement")
