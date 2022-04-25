"""create agent

Revision ID: 4a17754861c5
Revises: 843560323f85
Create Date: 2022-02-14 22:58:56.531143

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a17754861c5'
down_revision = '843560323f85'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'messages',
        sa.Column(
                    'id',
                    sa.Integer,
                    primary_key=True,
                    nullable=False
        ),
        sa.Column('task', sa.Integer, sa.ForeignKey('tasks.id'), nullable=False),
        sa.Column('variant', sa.Integer, sa.ForeignKey('variants.id'), nullable=False),
        sa.Column('group', sa.Integer, sa.ForeignKey('groups.id'), nullable=False),
        sa.Column('time', sa.DateTime, nullable=False),
        sa.Column('code', sa.String, nullable=False),
        sa.Column('ip', sa.String, nullable=False),
        sa.Column('processed', sa.Boolean, nullable=False)
    )


def downgrade():
    op.drop_table('messages')
