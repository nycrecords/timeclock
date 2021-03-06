"""Initial Migration - v2

Revision ID: 1d2cb52e1efb
Revises: 14543090feb
Create Date: 2017-06-28 20:56:57.002622

"""

# revision identifiers, used by Alembic.
revision = "1d2cb52e1efb"
down_revision = "14543090feb"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "change_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("changer_id", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("old", sa.String(length=128), nullable=True),
        sa.Column("new", sa.String(length=128), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["changer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "vacation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("start", sa.DateTime(), nullable=True),
        sa.Column("end", sa.DateTime(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column("pending", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("events", sa.Column("approved", sa.Boolean(), nullable=True))
    op.add_column("events", sa.Column("pending", sa.Boolean(), nullable=True))
    op.add_column("events", sa.Column("timepunch", sa.Boolean(), nullable=True))
    op.add_column("users", sa.Column("budget_code", sa.String(), nullable=True))
    op.add_column("users", sa.Column("is_supervisor", sa.Boolean(), nullable=True))
    op.add_column("users", sa.Column("object_code", sa.String(), nullable=True))
    op.add_column("users", sa.Column("object_name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("supervisor_id", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "users", "users", ["supervisor_id"], ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "users", type_="foreignkey")
    op.drop_column("users", "supervisor_id")
    op.drop_column("users", "object_name")
    op.drop_column("users", "object_code")
    op.drop_column("users", "is_supervisor")
    op.drop_column("users", "budget_code")
    op.drop_column("events", "timepunch")
    op.drop_column("events", "pending")
    op.drop_column("events", "approved")
    op.drop_table("vacation")
    op.drop_table("change_log")
    # ### end Alembic commands ###
