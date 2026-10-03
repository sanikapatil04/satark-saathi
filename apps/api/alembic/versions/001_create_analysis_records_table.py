"""create analysis_records table

Revision ID: 001_create_analysis_records
Revises:
Create Date: 2026-10-03 23:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_create_analysis_records'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'analysis_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('input_text', sa.Text(), nullable=False),
        sa.Column('verdict', sa.String(length=20), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('red_flags', sa.JSON(), nullable=False),
        sa.Column('recommended_action', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('analysis_records')
