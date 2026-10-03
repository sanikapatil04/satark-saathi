"""add source column to analysis_records

Revision ID: 002_add_source
Revises: 001_create_analysis_records
Create Date: 2026-10-03 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_add_source"
down_revision: Union[str, None] = "001_create_analysis_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "analysis_records",
        sa.Column("source", sa.String(length=20), nullable=False, server_default="TEXT"),
    )
    op.alter_column("analysis_records", "source", server_default=None)


def downgrade() -> None:
    op.drop_column("analysis_records", "source")
