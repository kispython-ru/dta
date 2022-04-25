"""fix task statuses

Revision ID: 448eb9809b1e
Revises: 4a17754861c5
Create Date: 2022-03-12 16:37:35.130079

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '448eb9809b1e'
down_revision = '4a17754861c5'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('task_statuses', 'title', new_column_name='group')


def downgrade():
    op.alter_column('task_statuses', 'group', new_column_name='title')
