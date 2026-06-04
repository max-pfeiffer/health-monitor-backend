"""add blood_pressure, blood_glucose and ketones models

Revision ID: af5af3559282
Revises:
Create Date: 2026-06-04

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "af5af3559282"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "blood_pressure",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("systolic", sa.Integer(), nullable=False),
        sa.Column("diastolic", sa.Integer(), nullable=False),
        sa.Column("pulse", sa.Integer(), nullable=True),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
    )
    op.create_table(
        "blood_glucose",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("value", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
    )
    op.create_table(
        "ketones",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("value", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ketones")
    op.drop_table("blood_glucose")
    op.drop_table("blood_pressure")
