"""add pending tag to events

Revision ID: 2cf6de142ea
Revises: 5b874b768e
Create Date: 2016-08-10 10:18:24.781996

"""

# revision identifiers, used by Alembic.
revision = '2cf6de142ea'
down_revision = '5b874b768e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('pending', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'pending')
    ### end Alembic commands ###