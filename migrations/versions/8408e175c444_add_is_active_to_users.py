"""Add is_active to users

Revision ID: 8408e175c444
Revises: 1d2cb52e1efb
Create Date: 2019-07-06 15:49:05.362634

"""

# revision identifiers, used by Alembic.
revision = '8408e175c444'
down_revision = '1d2cb52e1efb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'is_active')
    # ### end Alembic commands ###