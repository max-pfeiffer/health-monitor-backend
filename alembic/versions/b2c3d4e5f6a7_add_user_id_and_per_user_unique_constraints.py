"""add user_id column and per-user unique constraints on measured_at

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-09

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table, constraint_name in [
        ("blood_pressure", "uq_blood_pressure_user_measured_at"),
        ("blood_glucose", "uq_blood_glucose_user_measured_at"),
        ("ketones", "uq_ketones_user_measured_at"),
    ]:
        op.add_column(
            table,
            sa.Column(
                "user_id",
                sa.String(),
                nullable=False,
                server_default="",
            ),
        )
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])
        op.create_unique_constraint(constraint_name, table, ["user_id", "measured_at"])

    # drop the old per-table unique indexes on measured_at alone
    op.drop_index("ix_blood_pressure_measured_at", table_name="blood_pressure")
    op.drop_index("ix_blood_glucose_measured_at", table_name="blood_glucose")
    op.drop_index("ix_ketones_measured_at", table_name="ketones")

    # recreate as non-unique indexes (still useful for range queries)
    op.create_index("ix_blood_pressure_measured_at", "blood_pressure", ["measured_at"])
    op.create_index("ix_blood_glucose_measured_at", "blood_glucose", ["measured_at"])
    op.create_index("ix_ketones_measured_at", "ketones", ["measured_at"])

    # remove server defaults now that existing rows are backfilled
    for table in ("blood_pressure", "blood_glucose", "ketones"):
        op.alter_column(table, "user_id", server_default=None)


def downgrade() -> None:
    for table, constraint_name in [
        ("blood_pressure", "uq_blood_pressure_user_measured_at"),
        ("blood_glucose", "uq_blood_glucose_user_measured_at"),
        ("ketones", "uq_ketones_user_measured_at"),
    ]:
        op.drop_constraint(constraint_name, table, type_="unique")
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_column(table, "user_id")

    op.drop_index("ix_blood_pressure_measured_at", table_name="blood_pressure")
    op.drop_index("ix_blood_glucose_measured_at", table_name="blood_glucose")
    op.drop_index("ix_ketones_measured_at", table_name="ketones")

    op.create_index(
        "ix_blood_pressure_measured_at", "blood_pressure", ["measured_at"], unique=True
    )
    op.create_index(
        "ix_blood_glucose_measured_at", "blood_glucose", ["measured_at"], unique=True
    )
    op.create_index("ix_ketones_measured_at", "ketones", ["measured_at"], unique=True)
