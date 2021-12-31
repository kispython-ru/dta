"""create users

Revision ID: 297fea91dc9c
Revises:
Create Date: 2021-12-30 19:54:53.081441

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '297fea91dc9c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('email', sa.String, unique=True, nullable=False),
        sa.Column('password', sa.String, nullable=False)
    )


def downgrade():
    op.drop_table('users')
