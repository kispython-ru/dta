"""create webapp

Revision ID: 843560323f85
Revises:
Create Date: 2022-02-14 22:58:54.885726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '843560323f85'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'groups',
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("title", sa.String, unique=True, nullable=False),
    )
    op.create_table(
        'tasks',
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("title", sa.String, unique=True, nullable=False),
    )
    op.create_table(
        'variants',
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
    )
    op.create_table(
        'task_statuses',
        sa.Column('task', sa.Integer, sa.ForeignKey('tasks.id'), primary_key=True, nullable=False),
        sa.Column('variant', sa.Integer, sa.ForeignKey('variants.id'), primary_key=True, nullable=False),
        sa.Column('title', sa.Integer, sa.ForeignKey('groups.id'), primary_key=True, nullable=False),
        sa.Column('time', sa.DateTime, nullable=False),
        sa.Column('code', sa.String, nullable=False),
        sa.Column('output', sa.String, nullable=True),
        sa.Column('status', sa.Integer, nullable=False)
    )


def downgrade():
    op.drop_table('groups')
    op.drop_table('tasks')
    op.drop_table('variants')
    op.drop_table('task_statuses')
