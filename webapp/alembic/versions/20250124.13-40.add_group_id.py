"""add_group_id

Revision ID: 97b339c4e159
Revises: c9cc6ddcb46a
Create Date: 2025-01-24 13:40:44.771578

"""
from alembic import op
from alembic.operations.batch import BatchOperationsImpl
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '97b339c4e159'
down_revision = 'c9cc6ddcb46a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('students') as bop:
        bop.drop_column('group')
        bop.add_column(sa.Column('group', sa.Integer, nullable=True))
        bop.create_foreign_key('group', 'groups', ['group'], ['id'])


def downgrade():
    op.drop_column('students', 'group')
    op.add_column('students', sa.Column('group', sa.String, nullable=True))
