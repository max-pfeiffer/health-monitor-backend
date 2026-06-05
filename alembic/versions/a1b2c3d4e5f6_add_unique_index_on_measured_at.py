"""add unique index on measured_at for all health metric tables

Revision ID: a1b2c3d4e5f6
Revises: af5af3559282
Create Date: 2026-06-05

"""

from typing import Sequence, Union

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "af5af3559282"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_blood_pressure_measured_at",
        "blood_pressure",
        ["measured_at"],
        unique=True,
    )
    op.create_index(
        "ix_blood_glucose_measured_at",
        "blood_glucose",
        ["measured_at"],
        unique=True,
    )
    op.create_index(
        "ix_ketones_measured_at",
        "ketones",
        ["measured_at"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_ketones_measured_at", table_name="ketones")
    op.drop_index("ix_blood_glucose_measured_at", table_name="blood_glucose")
    op.drop_index("ix_blood_pressure_measured_at", table_name="blood_pressure")
