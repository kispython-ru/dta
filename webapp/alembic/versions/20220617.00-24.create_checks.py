"""create checks

Revision ID: 1333575b4d28
Revises: 41afa0763cca
Create Date: 2022-06-17 00:24:31.487138

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1333575b4d28'
down_revision = '41afa0763cca'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'message_checks',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('message', sa.Integer, sa.ForeignKey('messages.id'), nullable=False),
        sa.Column('time', sa.DateTime, nullable=False),
        sa.Column('status', sa.Integer, nullable=False),
        sa.Column('output', sa.String, nullable=True),
    )


def downgrade():
    op.drop_table('message_checks')
