"""initial migration

Revision ID: 001
Revises:
Create Date: 2026-07-02

"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hospitals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hpid", sa.String(20), nullable=False),
        sa.Column("dutyName", sa.String(100), nullable=False),
        sa.Column("dutyAddr", sa.String(200), nullable=True),
        sa.Column("dutyTel1", sa.String(20), nullable=True),
        sa.Column("hvec", sa.Integer(), nullable=True),
        sa.Column("hvoc", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hpid"),
    )


def downgrade() -> None:
    op.drop_table("hospitals")
