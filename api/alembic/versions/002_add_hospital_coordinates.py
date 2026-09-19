"""add hospital lat/lng columns

Revision ID: 002
Revises: 001
Create Date: 2026-09-19

"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("hospitals", sa.Column("lat", sa.Float(), nullable=True))
    op.add_column("hospitals", sa.Column("lng", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("hospitals", "lng")
    op.drop_column("hospitals", "lat")
