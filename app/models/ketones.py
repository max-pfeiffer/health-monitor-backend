from datetime import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Ketones(SQLModel, table=True):
    __tablename__ = "ketones"
    __table_args__ = (
        sa.UniqueConstraint(
            "user_id", "measured_at", name="uq_ketones_user_measured_at"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    value: Decimal = Field(
        sa_column=sa.Column(sa.Numeric(precision=5, scale=2), nullable=False)
    )
    measured_at: datetime = Field(index=True)
    notes: Optional[str] = None
