"""create_tasks

Revision ID: 120c3fbef9e1
Revises: 297fea91dc9c
Create Date: 2021-12-31 21:38:25.292910

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '120c3fbef9e1'
down_revision = '297fea91dc9c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('name', sa.String, unique=True, nullable=False),
    )
    op.create_table(
        'user_tasks',
        sa.Column(
            'user_id',
            sa.Integer,
            sa.ForeignKey('users.id'),
            primary_key=True,
            nullable=False),
        sa.Column(
            'task_id',
            sa.Integer,
            sa.ForeignKey('tasks.id'),
            primary_key=True,
            nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime,
            nullable=False),
        sa.Column(
            'status',
            sa.Integer,
            nullable=False),
        sa.UniqueConstraint(
            'user_id',
            'task_id',
            name='user_task_unique_constraint'))


def downgrade():
    op.drop_table('tasks')
    op.drop_table('user_tasks')
